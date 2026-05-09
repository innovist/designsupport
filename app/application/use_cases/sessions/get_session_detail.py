"""
Use-case: retrieve full session detail including brief.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.infrastructure.repositories.session_repository import SessionRepository
from app.models.session import DesignSession

logger = get_logger(__name__)


def get_session_detail(db: Session, session_id: uuid.UUID) -> DesignSession:
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    logger.info("[SESSION] detail loaded session=%s stage=%s status=%s",
                session_id, session.pipeline_stage, session.status)
    return session
