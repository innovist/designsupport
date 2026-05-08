"""Design session domain events.

Events raised during session lifecycle operations.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
from uuid import UUID
from typing import Optional

from apps.design_sessions.domain.value_objects import SessionStatus, SessionMode, PipelineStep


@dataclass
class SessionCreated:
    """Event raised when a design session is created."""

    session_id: UUID
    project_id: UUID
    mode: SessionMode
    started_by: UUID
    created_at: datetime

    def __init__(
        self,
        session_id: UUID,
        project_id: UUID,
        mode: SessionMode,
        started_by: UUID,
        created_at: Optional[datetime] = None,
    ):
        """Initialize session created event."""
        self.session_id = session_id
        self.project_id = project_id
        self.mode = mode
        self.started_by = started_by
        self.created_at = created_at or _utcnow()


@dataclass
class SessionStatusChanged:
    """Event raised when session status changes."""

    session_id: UUID
    project_id: UUID
    old_status: SessionStatus
    new_status: SessionStatus
    current_step: PipelineStep
    changed_at: datetime

    def __init__(
        self,
        session_id: UUID,
        project_id: UUID,
        old_status: SessionStatus,
        new_status: SessionStatus,
        current_step: PipelineStep,
        changed_at: Optional[datetime] = None,
    ):
        """Initialize status changed event."""
        self.session_id = session_id
        self.project_id = project_id
        self.old_status = old_status
        self.new_status = new_status
        self.current_step = current_step
        self.changed_at = changed_at or _utcnow()


@dataclass
class DecisionMade:
    """Event raised when a decision is recorded."""

    session_id: UUID
    step: PipelineStep
    action: str
    actor_kind: str
    actor_id: UUID
    rationale: str
    made_at: datetime

    def __init__(
        self,
        session_id: UUID,
        step: PipelineStep,
        action: str,
        actor_kind: str,
        actor_id: UUID,
        rationale: str,
        made_at: Optional[datetime] = None,
    ):
        """Initialize decision made event."""
        self.session_id = session_id
        self.step = step
        self.action = action
        self.actor_kind = actor_kind
        self.actor_id = actor_id
        self.rationale = rationale
        self.made_at = made_at or _utcnow()
