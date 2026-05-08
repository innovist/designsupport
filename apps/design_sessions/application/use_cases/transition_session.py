"""TransitionSession use case.

REQ-01-ORCH-001..004: State machine transitions with validation.
INV-01-04: Invalid transitions raise domain exception.
"""
from typing import List, Optional
from uuid import UUID

from apps.design_sessions.application.ports import (
    DecisionLogRepositoryPort,
    SessionRepositoryPort,
)
from apps.design_sessions.domain.entities import DecisionLog, DesignSession, PipelineStep
from apps.design_sessions.domain.services import SessionStateMachine
from apps.design_sessions.domain.value_objects import SessionStatus
from shared.application.decorators.audit import audit
from shared.domain.exceptions import NotFoundError, StateTransitionError


@audit(
    "design_session.transition",
    target_type_extractor=lambda **kw: "DesignSession",
    target_id_extractor=lambda **kw: str(kw.get("session_id", "")),
)
class TransitionSessionUseCase:
    """Transition a DesignSession to a new state.

    Validates the transition via SessionStateMachine, persists the updated
    session with select_for_update, and records a DecisionLog entry.
    """

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        decision_repository: DecisionLogRepositoryPort,
    ) -> None:
        self._session_repo = session_repository
        self._decision_repo = decision_repository

    async def execute(
        self,
        session_id: UUID,
        target_state: str,
        actor_kind: str,
        actor_id: UUID,
        rationale: str,
        evidence_refs: Optional[List[dict]] = None,
    ) -> DesignSession:
        """Execute state transition.

        Args:
            session_id: Session UUID
            target_state: Target state string value
            actor_kind: "user" or "auto"
            actor_id: UUID of actor
            rationale: Human-readable reason
            evidence_refs: Supporting evidence

        Returns:
            Updated DesignSession entity

        Raises:
            NotFoundError: Session not found
            StateTransitionError: Invalid transition
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(entity_type="DesignSession", identifier=str(session_id))

        try:
            target_status = SessionStatus(target_state)
        except ValueError:
            raise StateTransitionError(
                current_state=session.status.value,
                target_state=target_state,
            )

        # Validate via domain service
        if not SessionStateMachine.can_transition(session.status, target_status):
            raise StateTransitionError(
                current_state=session.status.value,
                target_state=target_state,
            )

        session.status = target_status
        from apps.design_sessions.domain.entities import _utcnow
        session.updated_at = _utcnow()

        saved = await self._session_repo.save(session)

        # Record decision log
        step_num = _state_to_step(target_status)
        decision = DecisionLog(
            session_id=session_id,
            step=step_num,
            action=f"transition_to_{target_state}",
            actor_kind=actor_kind,
            actor_id=actor_id,
            rationale=rationale,
            evidence_refs=evidence_refs or [],
        )
        await self._decision_repo.save(decision)

        return saved


def _state_to_step(status: SessionStatus) -> PipelineStep:
    """Map session status to representative PipelineStep."""
    mapping = {
        SessionStatus.QUEUED: PipelineStep.PURPOSE_INPUT,
        SessionStatus.RESEARCHING: PipelineStep.TREND_RESEARCH,
        SessionStatus.CONCEPTING: PipelineStep.CONCEPT_GENERATION,
        SessionStatus.REFERENCING: PipelineStep.REFERENCE_SEARCH,
        SessionStatus.ABSTRACTING: PipelineStep.SKETCH_ANALYSIS,
        SessionStatus.GENERATING: PipelineStep.GENERATION,
        SessionStatus.DOCUMENTING: PipelineStep.SPEC_DOCUMENT,
        SessionStatus.REVIEW_READY: PipelineStep.REVIEW,
        SessionStatus.FAILED: PipelineStep.PURPOSE_INPUT,
    }
    return mapping.get(status, PipelineStep.PURPOSE_INPUT)
