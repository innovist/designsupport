"""RerunFromStep use case.

AC-01-R-007: Preserves prior step artifacts; bumps version;
sets current_step to requested step; transitions status to that step's
mapped state per §5.4 table.
"""
from uuid import UUID

from apps.design_sessions.application.ports import (
    DecisionLogRepositoryPort,
    SessionRepositoryPort,
)
from apps.design_sessions.domain.entities import DecisionLog, DesignSession, PipelineStep
from apps.design_sessions.domain.value_objects import SessionStatus
from shared.application.decorators.audit import audit
from shared.domain.exceptions import NotFoundError, ValidationError


@audit(
    "design_session.rerun",
    target_type_extractor=lambda **kw: "DesignSession",
    target_id_extractor=lambda **kw: str(kw.get("session_id", "")),
)
class RerunFromStepUseCase:
    """Re-run session from a specific step.

    Bumps version, sets current_step, and transitions status to the
    state that corresponds to from_step per §5.4 mapping.
    Prior step artifacts are preserved (not deleted).
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
        from_step: int,
        actor_id: UUID,
        rationale: str = "",
    ) -> DesignSession:
        """Re-run session from a specific step number.

        Args:
            session_id: Session UUID
            from_step: Pipeline step number (1-17) to restart from
            actor_id: User UUID
            rationale: Reason for rerun

        Returns:
            Updated DesignSession

        Raises:
            NotFoundError: Session not found
            ValidationError: Invalid step number
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(entity_type="DesignSession", identifier=str(session_id))

        if not (1 <= from_step <= 17):
            raise ValidationError(field="from_step", message=f"Must be 1-17, got {from_step}")

        try:
            pipeline_step = PipelineStep(from_step)
        except ValueError:
            raise ValidationError(field="from_step", message=f"Invalid step: {from_step}")

        # Map step to target state per §5.4
        target_status = pipeline_step.get_session_status()

        # Bump version, set new step and status
        session.version += 1
        session.current_step = pipeline_step
        session.status = target_status
        from apps.design_sessions.domain.entities import _utcnow
        session.updated_at = _utcnow()

        saved = await self._session_repo.save(session)

        decision = DecisionLog(
            session_id=session_id,
            step=pipeline_step,
            action="rerun_from_step",
            actor_kind="user",
            actor_id=actor_id,
            rationale=rationale or f"Rerun from step {from_step}",
        )
        await self._decision_repo.save(decision)

        return saved
