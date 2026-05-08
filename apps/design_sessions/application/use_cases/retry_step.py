"""RetryStep use case.

REQ-01-ASYNC-002: Re-queues current step when status=failed.
Phase 2: Celery enqueueing deferred. For now transitions back to the
in-flight state prior to failure (queued).
"""
from uuid import UUID

from apps.design_sessions.application.ports import (
    DecisionLogRepositoryPort,
    SessionRepositoryPort,
)
from apps.design_sessions.domain.entities import DecisionLog, DesignSession, PipelineStep
from apps.design_sessions.domain.value_objects import SessionStatus
from shared.application.decorators.audit import audit
from shared.domain.exceptions import NotFoundError, StateTransitionError


@audit(
    "design_session.retry",
    target_type_extractor=lambda **kw: "DesignSession",
    target_id_extractor=lambda **kw: str(kw.get("session_id", "")),
)
class RetryStepUseCase:
    """Retry a failed session step.

    Transitions status from failed → queued, preserving current_step.
    Celery task enqueueing is deferred to Phase 2.
    """

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        decision_repository: DecisionLogRepositoryPort,
    ) -> None:
        self._session_repo = session_repository
        self._decision_repo = decision_repository

    async def execute(self, session_id: UUID, actor_id: UUID) -> DesignSession:
        """Retry from current failed step.

        Args:
            session_id: Session UUID
            actor_id: User requesting retry

        Returns:
            Updated session with status=queued

        Raises:
            NotFoundError: Session not found
            StateTransitionError: Session not in failed state
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(entity_type="DesignSession", identifier=str(session_id))

        if session.status != SessionStatus.FAILED:
            raise StateTransitionError(
                current_state=session.status.value,
                target_state="queued",
            )

        session.status = SessionStatus.QUEUED
        from apps.design_sessions.domain.entities import _utcnow
        session.updated_at = _utcnow()

        saved = await self._session_repo.save(session)

        decision = DecisionLog(
            session_id=session_id,
            step=session.current_step,
            action="retry",
            actor_kind="user",
            actor_id=actor_id,
            rationale="User-requested retry of failed step",
        )
        await self._decision_repo.save(decision)

        return saved
