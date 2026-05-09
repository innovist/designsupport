"""
Use-cases: create project and create session.
"""

import uuid

from sqlalchemy.orm import Session

from app.application.dtos.session_dtos import ProjectCreate, SessionCreate
from app.core.logging import get_logger
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.workspace_repository import WorkspaceRepository
from app.models.project import DesignProject
from app.models.session import DesignSession

logger = get_logger(__name__)


def create_project(db: Session, data: ProjectCreate) -> DesignProject:
    logger.info("[SESSION] create_project name=%s domain=%s", data.name, data.domain)
    workspace_repo = WorkspaceRepository(db)
    workspace = workspace_repo.ensure_default_workspace()

    project_repo = ProjectRepository(db)
    project = project_repo.create(
        workspace_id=workspace.id,
        name=data.name,
        domain=data.domain,
        purpose=data.purpose,
    )
    logger.info("[SESSION] project created id=%s", project.id)
    return project


def create_session(db: Session, data: SessionCreate) -> DesignSession:
    logger.info("[SESSION] create_session project_id=%s mode=%s", data.project_id, data.mode)
    session_repo = SessionRepository(db)
    session = session_repo.create(
        project_id=data.project_id,
        mode=data.mode,
    )
    logger.info("[SESSION] session created id=%s pipeline_stage=%s", session.id, session.pipeline_stage)
    return session
