"""
Use-case: reset a session pipeline_stage to allow re-running from that step.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.infrastructure.repositories.session_repository import SessionRepository
from app.models.session import DesignSession

logger = get_logger(__name__)

_VALID_STAGES = {
    "brief",
    "brief_input",
    "queued",
    "trend",
    "researching",
    "concepts",
    "concepting",
    "references",
    "referencing",
    "abstracting", "generating", "documenting", "review_ready",
}


def rerun_step(db: Session, session_id: uuid.UUID, stage: str) -> DesignSession:
    if stage not in _VALID_STAGES:
        raise ValueError(f"Invalid stage '{stage}'. Valid: {sorted(_VALID_STAGES)}")

    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    prev_stage = session.pipeline_stage
    session.pipeline_stage = stage
    session.status = "active"
    db.commit()
    db.refresh(session)
    logger.info("[SESSION] rerun session=%s stage=%s -> %s", session_id, prev_stage, stage)
    return session
