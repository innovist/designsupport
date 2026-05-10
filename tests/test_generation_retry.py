"""Tests for image generation retry behavior."""

import uuid

import pytest
from fastapi import BackgroundTasks

from app.application.dtos.generation_dtos import GenerationRequest
from app.application.use_cases.generation import create_generation_job as generation_job_module
from app.application.use_cases.generation.create_generation_job import (
    create_generation_job,
    retry_generation_job,
)
from app.application.use_cases.specs.generate_spec import generate_spec
from app.core.database import SessionLocal, engine
from app.infrastructure.ai_clients.zimage_client import _dashscope_size
from app.models.abstraction import AbstractionRule
from app.models.base import Base
from app.models.concepts import ConceptCandidate
from app.models.generation import GeneratedDesign
from app.models.project import DesignProject
from app.models.session import DesignSession
from app.models.workspace import Workspace


@pytest.fixture()
def db_session():
    if engine.url.get_backend_name() != "sqlite":
        raise RuntimeError(f"generation retry tests must not run against {engine.url}")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        yield db


def test_dashscope_size_uses_asterisk_separator():
    assert _dashscope_size("1024x1024") == "1024*1024"
    assert _dashscope_size("1536×1024") == "1536*1024"
    assert _dashscope_size("832*1248") == "832*1248"


@pytest.mark.asyncio
async def test_create_generation_job_allows_concept_only_draft(db_session, monkeypatch):
    workspace = Workspace(name="Concept Draft Workspace")
    db_session.add(workspace)
    db_session.flush()
    project = DesignProject(workspace_id=workspace.id, name="Concept Draft Project")
    db_session.add(project)
    db_session.flush()
    session = DesignSession(project_id=project.id)
    db_session.add(session)
    db_session.flush()
    concept = ConceptCandidate(
        session_id=session.id,
        name="Soft hinge lamp",
        description="rounded hinge and warm translucent shade",
    )
    db_session.add(concept)
    db_session.commit()

    async def fake_prompt(*args, **kwargs):
        return "concept-only draft prompt"

    monkeypatch.setattr(generation_job_module, "build_generation_prompt", fake_prompt)

    tasks = BackgroundTasks()
    design = await create_generation_job(
        db_session,
        session.id,
        GenerationRequest(output_kind="draft", concept_id=concept.id),
        tasks,
    )

    assert design.rule_id is None
    assert design.concept_id == concept.id
    assert design.prompt == "concept-only draft prompt"
    assert design.status == "pending"
    assert len(tasks.tasks) == 1


def test_retry_generation_resets_failed_record(db_session):
    workspace = Workspace(name="Retry Workspace")
    db_session.add(workspace)
    db_session.flush()

    project = DesignProject(workspace_id=workspace.id, name="Retry Project")
    db_session.add(project)
    db_session.flush()

    session = DesignSession(project_id=project.id)
    db_session.add(session)
    db_session.flush()

    rule = AbstractionRule(
        session_id=session.id,
        source_type="concept",
        source_id=uuid.uuid4(),
        form="compact silhouette",
        structure="two-piece hinge",
        axes_count=2,
    )
    db_session.add(rule)
    db_session.flush()

    design = GeneratedDesign(
        session_id=session.id,
        rule_id=rule.id,
        prompt="product draft prompt",
        status="failed",
        failure_reason="provider error",
        provider="alibaba",
        model="z-image-turbo",
        image_path="broken.png",
        generation_params={"output_kind": "draft"},
    )
    db_session.add(design)
    db_session.commit()

    tasks = BackgroundTasks()
    retried = retry_generation_job(db_session, design.id, tasks)

    assert retried.status == "pending"
    assert retried.failure_reason is None
    assert retried.provider is None
    assert retried.model is None
    assert retried.image_path is None
    assert retried.generation_params["output_kind"] == "draft"
    assert retried.generation_params["retry_of"] == str(design.id)
    assert len(tasks.tasks) == 1


def test_retry_generation_rejects_completed_record(db_session):
    workspace = Workspace(name="Retry Workspace")
    db_session.add(workspace)
    db_session.flush()
    project = DesignProject(workspace_id=workspace.id, name="Retry Project")
    db_session.add(project)
    db_session.flush()
    session = DesignSession(project_id=project.id)
    db_session.add(session)
    db_session.flush()
    rule = AbstractionRule(
        session_id=session.id,
        source_type="concept",
        form="compact silhouette",
        structure="two-piece hinge",
        axes_count=2,
    )
    db_session.add(rule)
    db_session.flush()
    design = GeneratedDesign(
        session_id=session.id,
        rule_id=rule.id,
        prompt="product draft prompt",
        status="completed",
        image_path="generated/ok.png",
    )
    db_session.add(design)
    db_session.commit()

    with pytest.raises(ValueError):
        retry_generation_job(db_session, design.id, BackgroundTasks())


def test_generate_spec_tracks_selected_completed_design(db_session):
    workspace = Workspace(name="Report Workspace")
    db_session.add(workspace)
    db_session.flush()
    project = DesignProject(workspace_id=workspace.id, name="Report Project")
    db_session.add(project)
    db_session.flush()
    session = DesignSession(project_id=project.id)
    db_session.add(session)
    db_session.flush()

    draft = GeneratedDesign(
        session_id=session.id,
        prompt="draft prompt",
        status="completed",
        image_path="generated/draft.png",
        generation_params={"output_kind": "draft"},
    )
    final = GeneratedDesign(
        session_id=session.id,
        prompt="final prompt",
        status="completed",
        image_path="generated/final.png",
        generation_params={"output_kind": "final"},
    )
    db_session.add_all([draft, final])
    db_session.commit()

    spec = generate_spec(db_session, session.id, final.id)

    assert spec.selected_design_id == final.id
    assert spec.content_json["selected_design"]["id"] == str(final.id)
    assert spec.content_json["selected_design"]["output_kind"] == "final"


def test_generate_spec_rejects_unfinished_selected_design(db_session):
    workspace = Workspace(name="Report Workspace")
    db_session.add(workspace)
    db_session.flush()
    project = DesignProject(workspace_id=workspace.id, name="Report Project")
    db_session.add(project)
    db_session.flush()
    session = DesignSession(project_id=project.id)
    db_session.add(session)
    db_session.flush()

    design = GeneratedDesign(
        session_id=session.id,
        prompt="pending prompt",
        status="pending",
        generation_params={"output_kind": "final"},
    )
    db_session.add(design)
    db_session.commit()

    with pytest.raises(ValueError):
        generate_spec(db_session, session.id, design.id)
