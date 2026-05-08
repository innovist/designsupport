"""Design session domain entities.

Core session orchestration entities with state machine logic.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List

from apps.design_sessions.domain.value_objects import SessionStatus, SessionMode, PipelineStep


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# @MX:ANCHOR: [AUTO] DesignSession aggregate root - core session entity
# @MX:REASON: High fan_in - used by all session use cases, repositories, and API views
@dataclass
class DesignSession:
    """Design session aggregate root.

    Orchestrates the entire design creation pipeline with state management.
    """

    id: UUID
    project_id: UUID
    mode: SessionMode
    status: SessionStatus
    current_step: PipelineStep
    version: int
    started_by: UUID
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        project_id: UUID,
        started_by: UUID,
        mode: SessionMode = SessionMode.GUIDED,
        status: SessionStatus = SessionStatus.QUEUED,
        current_step: PipelineStep = PipelineStep.PURPOSE_INPUT,
        version: int = 1,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize a new design session.

        Args:
            project_id: Parent project UUID
            started_by: User who started the session
            mode: Execution mode (guided/auto)
            status: Initial status
            current_step: Current pipeline step
            version: Session version for re-runs
            id: Session UUID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id or uuid4()
        self.project_id = project_id
        self.mode = mode
        self.status = status
        self.current_step = current_step
        self.version = version
        self.started_by = started_by
        self.created_at = created_at or _utcnow()
        self.updated_at = updated_at or _utcnow()

    # @MX:ANCHOR: [AUTO] State transition with validation guard
    # @MX:REASON: High fan_in - called by orchestrator, use cases, state machine
    def transition_to(self, new_status: SessionStatus) -> None:
        """Transition to a new status.

        Args:
            new_status: Target status

        Raises:
            ValueError: If transition is invalid per state machine
        """
        from apps.design_sessions.domain.services import SessionStateMachine

        if not SessionStateMachine.can_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition: {self.status.value} -> {new_status.value}")

        self.status = new_status
        self.updated_at = _utcnow()

    def advance_step(self) -> None:
        """Advance to next pipeline step."""
        step_values = list(PipelineStep)
        current_index = step_values.index(self.current_step)
        if current_index < len(step_values) - 1:
            self.current_step = step_values[current_index + 1]
            self.updated_at = _utcnow()

    def fail(self, reason: str) -> None:
        """Mark session as failed.

        Args:
            reason: Failure reason
        """
        self.status = SessionStatus.FAILED
        self.updated_at = _utcnow()


@dataclass
class DesignBrief:
    """Design brief entity.

    Contains structured design requirements and constraints.
    """

    id: UUID
    session_id: UUID
    purpose: str
    audience: str
    usage_context: str
    constraints: str
    result_form: str
    clarifying_questions: List[Dict[str, Any]]
    score: float

    def __init__(
        self,
        session_id: UUID,
        purpose: str,
        audience: str,
        usage_context: str,
        constraints: str,
        result_form: str,
        clarifying_questions: Optional[List[Dict[str, Any]]] = None,
        score: float = 0.0,
        id: Optional[UUID] = None,
    ):
        """Initialize a design brief.

        Args:
            session_id: Parent session UUID
            purpose: Design purpose statement
            audience: Target audience description
            usage_context: Usage context information
            constraints: Design constraints
            result_form: Expected result format
            clarifying_questions: Questions for missing information
            score: Brief completeness score (0-1)
            id: Brief UUID
        """
        self.id = id or uuid4()
        self.session_id = session_id
        self.purpose = purpose
        self.audience = audience
        self.usage_context = usage_context
        self.constraints = constraints
        self.result_form = result_form
        self.clarifying_questions = clarifying_questions or []
        self.score = score

    # @MX:NOTE: [AUTO] Brief completeness check - gates workflow progression
    # @MX:REASON: Business rule - session cannot proceed until questions are answered
    def needs_clarification(self) -> bool:
        """Check if brief needs user clarification.

        Returns:
            True if clarifying questions exist
        """
        return len(self.clarifying_questions) > 0


# @MX:NOTE: [AUTO] Immutable decision log - append-only audit trail
# @MX:REASON: Domain invariant - decisions are permanent for traceability
@dataclass
class DecisionLog:
    """Decision log entity.

    Records all decisions made during session execution.
    Supports both user and auto decisions.
    """

    id: UUID
    session_id: UUID
    step: PipelineStep
    action: str
    actor_kind: str  # 'user' or 'auto'
    actor_id: UUID
    rationale: str
    evidence_refs: List[Dict[str, Any]]
    created_at: datetime

    def __init__(
        self,
        session_id: UUID,
        step: PipelineStep,
        action: str,
        actor_kind: str,
        actor_id: UUID,
        rationale: str,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize a decision log entry.

        Args:
            session_id: Parent session UUID
            step: Pipeline step when decision was made
            action: Action description
            actor_kind: 'user' or 'auto'
            actor_id: Actor UUID (user_id or system ID)
            rationale: Decision rationale
            evidence_refs: Supporting evidence references
            id: Log entry UUID
            created_at: Timestamp
        """
        self.id = id or uuid4()
        self.session_id = session_id
        self.step = step
        self.action = action
        self.actor_kind = actor_kind
        self.actor_id = actor_id
        self.rationale = rationale
        self.evidence_refs = evidence_refs or []
        self.created_at = created_at or _utcnow()
