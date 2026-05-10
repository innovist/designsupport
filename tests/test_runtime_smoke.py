"""Runtime smoke tests for the FastAPI user-facing workflow."""

import os
import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from main import app  # noqa: E402
from app.core.database import engine  # noqa: E402
from app.models.base import Base  # noqa: E402
importlib.import_module("app.models")


# @MX:NOTE: [AUTO] Test fixture factory - creates clean database schema for each test
def _client() -> TestClient:
    if engine.url.get_backend_name() != "sqlite":
        raise RuntimeError(f"runtime smoke tests must not run against {engine.url}")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


def test_public_pages_render():
    with _client() as client:
        paths = ["/", "/workspace", "/workspace/settings", "/projects", "/library"]
        for path in paths:
            response = client.get(path)
            assert response.status_code == 200, path


def test_project_session_brief_spec_flow():
    with _client() as client:
        project = client.post(
            "/api/projects",
            json={
                "name": "Runtime Project",
                "domain": "industrial",
                "purpose": "Compact desk phone stand",
            },
        )
        assert project.status_code == 201
        project_id = project.json()["id"]

        session = client.post(
            "/api/sessions",
            json={"project_id": project_id, "mode": "chatbot"},
        )
        assert session.status_code == 201
        session_id = session.json()["id"]

        brief = client.post(
            f"/api/sessions/{session_id}/brief",
            json={
                "purpose": "Compact desk phone stand",
                "domain": "industrial",
                "target_user": "Office workers",
                "context": "Small work desk",
                "constraints": "Ceramic or recycled plastic",
                "use_case": "Vertical and horizontal phone support",
                "result_form": "concept sketch",
            },
        )
        assert brief.status_code == 200
        assert brief.json()["is_complete"] is True

        detail = client.get(f"/api/sessions/{session_id}")
        assert detail.status_code == 200
        assert detail.json()["brief"]["purpose"] == "Compact desk phone stand"

        spec = client.post(f"/api/sessions/{session_id}/specs")
        assert spec.status_code == 201
        content = spec.json()["content_json"]
        assert content["brief"]["purpose"] == "Compact desk phone stand"
        assert "discarded_alternatives" in content
        assert "sources" in content


def test_settings_api_does_not_expose_raw_keys():
    with _client() as client:
        aliases = client.get("/api/workspace/api-key-aliases")
        assert aliases.status_code == 200
        payload = aliases.json()
        assert "configured_providers" in payload
        assert "api_key" not in str(payload).lower()

        models = client.get("/api/workspace/feature-models")
        assert models.status_code == 200
        keys = {item["feature_key"] for item in models.json()}
        assert {
            "abstraction",
            "sketch_prompt_generation",
            "sketch_generation",
            "final_image_prompt_generation",
            "final_image_generation",
            "sketch_analysis",
            "concept_generation",
            "chat",
            "image_generation",
            "reference_analysis",
            "brief_structuring",
            "spec_writing",
            "trend_analysis",
        } <= keys


def teardown_module():
    Path("test_runtime_smoke.db").unlink(missing_ok=True)
