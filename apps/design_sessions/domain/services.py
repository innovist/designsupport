"""Design session domain services.

State machine orchestration and session lifecycle management.
"""
from typing import Set, Optional
from uuid import UUID

from apps.design_sessions.domain.value_objects import SessionStatus, SessionMode, PipelineStep


# @MX:ANCHOR: [AUTO] Session state transition guard - SPEC-01 §5.3 compliance
# @MX:REASON: High fan_in - used by orchestrator, use cases, and API views
class SessionStateMachine:
    """State machine for design session status transitions.

    Enforces SPEC-01 §5.3 state machine rules.
    """

    # Valid transitions per state machine diagram
    _TRANSITIONS = {
        SessionStatus.QUEUED: {SessionStatus.RESEARCHING, SessionStatus.FAILED},
        SessionStatus.RESEARCHING: {SessionStatus.CONCEPTING, SessionStatus.FAILED},
        SessionStatus.CONCEPTING: {SessionStatus.REFERENCING, SessionStatus.FAILED},
        SessionStatus.REFERENCING: {SessionStatus.ABSTRACTING, SessionStatus.FAILED},
        SessionStatus.ABSTRACTING: {SessionStatus.GENERATING, SessionStatus.FAILED},
        SessionStatus.GENERATING: {SessionStatus.DOCUMENTING, SessionStatus.FAILED},
        SessionStatus.DOCUMENTING: {SessionStatus.REVIEW_READY, SessionStatus.FAILED},
        SessionStatus.REVIEW_READY: set(),  # Terminal state
        SessionStatus.FAILED: {
            SessionStatus.QUEUED,  # Retry from start
            SessionStatus.RESEARCHING,  # Retry from researching
            SessionStatus.CONCEPTING,  # Retry from concepting
            SessionStatus.REFERENCING,  # Retry from referencing
            SessionStatus.ABSTRACTING,  # Retry from abstracting
            SessionStatus.GENERATING,  # Retry from generating
        },
    }

    @classmethod
    # @MX:ANCHOR: [AUTO] State transition validation - prevents invalid state changes
    # @MX:REASON: High fan_in - called by entity.transition_to, orchestrator, use cases
    def can_transition(cls, from_status: SessionStatus, to_status: SessionStatus) -> bool:
        """Check if status transition is valid.

        Args:
            from_status: Current status
            to_status: Target status

        Returns:
            True if transition is allowed per state machine
        """
        return to_status in cls._TRANSITIONS.get(from_status, set())

    @classmethod
    def validate_transition(cls, from_status: SessionStatus, to_status: SessionStatus) -> None:
        """Validate status transition.

        Args:
            from_status: Current status
            to_status: Target status

        Raises:
            ValueError: If transition is invalid
        """
        if not cls.can_transition(from_status, to_status):
            raise ValueError(
                f"Invalid state transition: {from_status.value} -> {to_status.value}. "
                f"Allowed: {[s.value for s in cls._TRANSITIONS.get(from_status, set())]}"
            )

    @classmethod
    def get_allowed_transitions(cls, from_status: SessionStatus) -> Set[SessionStatus]:
        """Get all allowed transitions from a status.

        Args:
            from_status: Current status

        Returns:
            Set of allowed target statuses
        """
        return cls._TRANSITIONS.get(from_status, set()).copy()

    @classmethod
    def get_retry_targets(cls, failed_at: SessionStatus) -> Set[SessionStatus]:
        """Get valid retry targets after failure.

        Args:
            failed_at: Status where failure occurred

        Returns:
            Set of statuses that can be used for retry
        """
        # From failed state, can retry to any step up to and including failed step
        if failed_at == SessionStatus.FAILED:
            return cls._TRANSITIONS[SessionStatus.FAILED].copy()

        # If currently in failed state, determine what caused the failure
        # For simplicity, return all possible retry states
        return cls._TRANSITIONS[SessionStatus.FAILED].copy()

    @classmethod
    def should_auto_progress(cls, mode: SessionMode, current_status: SessionStatus) -> bool:
        """Determine if session should auto-progress.

        Args:
            mode: Session execution mode
            current_status: Current session status

        Returns:
            True if auto-progression is enabled
        """
        if mode != SessionMode.AUTO:
            return False

        # Auto mode progresses through all non-terminal states
        return current_status not in {SessionStatus.REVIEW_READY, SessionStatus.FAILED}

    @classmethod
    def get_next_status(cls, current_status: SessionStatus, mode: SessionMode) -> Optional[SessionStatus]:
        """Get next status for auto-progression.

        Args:
            current_status: Current session status
            mode: Session execution mode

        Returns:
            Next status or None if terminal
        """
        if not cls.should_auto_progress(mode, current_status):
            return None

        # Get allowed transitions
        allowed = cls.get_allowed_transitions(current_status)

        # Filter out failed state (only use on actual failure)
        allowed.discard(SessionStatus.FAILED)

        # Return the single remaining transition
        return allowed.pop() if allowed else None

    @classmethod
    def can_rerun_from_step(cls, current_status: SessionStatus, step: PipelineStep) -> bool:
        """Check if session can be re-run from a specific step.

        Args:
            current_status: Current session status
            step: Step to re-run from

        Returns:
            True if re-run is allowed
        """
        # Can only re-run from steps that map to earlier or current status
        step_status = step.get_session_status()

        # If session failed, can re-run from any step up to failure point
        if current_status == SessionStatus.FAILED:
            return True

        # Otherwise, must be from earlier or same status
        status_order = [
            SessionStatus.QUEUED,
            SessionStatus.RESEARCHING,
            SessionStatus.CONCEPTING,
            SessionStatus.REFERENCING,
            SessionStatus.ABSTRACTING,
            SessionStatus.GENERATING,
            SessionStatus.DOCUMENTING,
            SessionStatus.REVIEW_READY,
        ]

        try:
            current_idx = status_order.index(current_status)
            step_idx = status_order.index(step_status)
            return step_idx <= current_idx
        except ValueError:
            return False


# @MX:ANCHOR: [AUTO] Session workflow orchestration service
# @MX:REASON: High fan_in - used by create session use case, orchestrator, retry flows
class SessionWorkflowService:
    """Service for session workflow operations."""

    @staticmethod
    # @MX:NOTE: [AUTO] Session factory method - used by CreateSessionUseCase
    # @MX:REASON: Demoted from ANCHOR (per-file limit 3); fan_in=2, below threshold
    def create_session(
        project_id: UUID,
        started_by: UUID,
        mode: SessionMode = SessionMode.GUIDED,
    ) -> "DesignSession":
        """Create a new design session.

        Args:
            project_id: Parent project UUID
            started_by: User who started the session
            mode: Execution mode

        Returns:
            New DesignSession instance
        """
        from apps.design_sessions.domain.entities import DesignSession

        return DesignSession(
            project_id=project_id,
            started_by=started_by,
            mode=mode,
            status=SessionStatus.QUEUED,
            current_step=PipelineStep.PURPOSE_INPUT,
        )

    @staticmethod
    def advance_session(
        session: "DesignSession",
        new_status: Optional[SessionStatus] = None,
    ) -> None:
        """Advance session to next status/step.

        Args:
            session: DesignSession to advance
            new_status: Explicit target status (auto-calculated if None)
        """
        if new_status is None:
            new_status = SessionStateMachine.get_next_status(session.mode, session.status)

        if new_status is None:
            return  # Terminal state or manual progression needed

        session.transition_to(new_status)
        if new_status != SessionStatus.FAILED:
            session.advance_step()

    @staticmethod
    def handle_failure(
        session: "DesignSession",
        failure_reason: str,
        failed_step: Optional[PipelineStep] = None,
    ) -> None:
        """Handle session failure.

        Args:
            session: DesignSession that failed
            failure_reason: Description of failure
            failed_step: Step where failure occurred
        """
        session.fail(failure_reason)
        if failed_step:
            session.current_step = failed_step

    @staticmethod
    def retry_from_step(
        session: "DesignSession",
        retry_step: PipelineStep,
    ) -> None:
        """Retry session from a specific step.

        Args:
            session: DesignSession to retry
            retry_step: Step to retry from

        Raises:
            ValueError: If retry is not allowed
        """
        if not SessionStateMachine.can_rerun_from_step(session.status, retry_step):
            raise ValueError(f"Cannot retry from step {retry_step.name} in status {session.status.value}")

        # Reset to queued and update step
        session.status = SessionStatus.QUEUED
        session.current_step = retry_step
        session.version += 1
