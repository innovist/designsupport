"""
Repository for DesignSession, DesignBrief, and ChatMessage.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.session import ChatMessage, DesignBrief, DesignSession


# @MX:ANCHOR: [AUTO] Session repository - primary data access layer for DesignSession entities
# @MX:REASON: High fan_in (15+ callers) - all session operations route through this repository

class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, project_id: uuid.UUID, mode: str = "chatbot") -> DesignSession:
        session = DesignSession(project_id=project_id, mode=mode)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(self, session_id: uuid.UUID) -> DesignSession | None:
        return (
            self.db.query(DesignSession)
            .filter_by(id=session_id)
            .first()
        )

    def list_for_project(self, project_id: uuid.UUID) -> list[DesignSession]:
        return (
            self.db.query(DesignSession)
            .filter_by(project_id=project_id)
            .order_by(DesignSession.created_at.desc())
            .all()
        )

    def update_stage(self, session_id: uuid.UUID, stage: str) -> DesignSession:
        session = self.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        session.pipeline_stage = stage
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_progress(self, session_id: uuid.UUID) -> dict:
        """Return pipeline progress snapshot for polling."""
        session = self.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        return {
            "pipeline_stage": session.pipeline_stage,
            "status": session.status,
            "mode": session.mode,
            "auto_progress_log": session.auto_progress_log or [],
        }

    def set_auto_mode(self, session_id: uuid.UUID) -> DesignSession:
        """Switch session to auto mode."""
        session = self.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        session.mode = "auto"
        self.db.commit()
        self.db.refresh(session)
        return session

    def upsert_brief(self, session_id: uuid.UUID, fields: dict) -> DesignBrief:
        brief = self.db.query(DesignBrief).filter_by(session_id=session_id).first()
        if not brief:
            purpose = fields.pop("purpose", None) or ""
            brief = DesignBrief(session_id=session_id, purpose=purpose, **fields)
            self.db.add(brief)
        else:
            for k, v in fields.items():
                if v is not None and hasattr(brief, k):
                    setattr(brief, k, v)
        self.db.commit()
        self.db.refresh(brief)
        return brief
