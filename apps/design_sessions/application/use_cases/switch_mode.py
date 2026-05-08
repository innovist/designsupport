"""SwitchMode use case.

AC-01-M-006: Mode switch (auto→guided) only allowed at step boundary.
Records a DecisionLog entry for mode_change.
"""
from uuid import UUID

from apps.design_sessions.application.ports import (
    DecisionLogRepositoryPort,
    SessionRepositoryPort,
)
from apps.design_sessions.domain.entities import DecisionLog, DesignSession, PipelineStep
from apps.design_sessions.domain.value_objects import SessionMode
from shared.application.decorators.audit import audit
from shared.domain.exceptions import NotFoundError, ValidationError


def _is_at_step_boundary(current_step: PipelineStep) -> bool:
    """Check if current_step is the LAST step in its status group.

    A 'safe halt point' is when the session is at the final step of
    the current state group (i.e., moving to a new state boundary).
    """
    start, end = current_step.get_step_range()
    return current_step.value == end


@audit(
    "design_session.switch_mode",
    target_type_extractor=lambda **kw: "DesignSession",
    target_id_extractor=lambda **kw: str(kw.get("session_id", "")),
)
class SwitchModeUseCase:
    """Switch session mode between auto and guided.

    auto→guided: only allowed when current_step is at a state boundary.
    guided→auto: always allowed.
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
        new_mode: str,
        actor_id: UUID,
        rationale: str = "",
    ) -> DesignSession:
        """Switch mode.

        Args:
            session_id: Session UUID
            new_mode: "guided" or "auto"
            actor_id: User UUID
            rationale: Optional rationale

        Returns:
            Updated DesignSession

        Raises:
            NotFoundError: Session not found
            ValidationError: If auto→guided while mid-step
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(entity_type="DesignSession", identifier=str(session_id))

        if new_mode not in {"guided", "auto"}:
            raise ValidationError(field="new_mode", message=f"Must be 'guided' or 'auto', got {new_mode!r}")

        target_mode = SessionMode(new_mode)

        if session.mode == SessionMode.AUTO and target_mode == SessionMode.GUIDED:
            if not _is_at_step_boundary(session.current_step):
                raise ValidationError(
                    field="mode",
                    message=(
                        "Cannot switch auto→guided while mid-step. "
                        f"Current step {session.current_step.value} is not at a state boundary."
                    ),
                )

        old_mode = session.mode.value
        session.mode = target_mode
        from apps.design_sessions.domain.entities import _utcnow
        session.updated_at = _utcnow()

        saved = await self._session_repo.save(session)

        decision = DecisionLog(
            session_id=session_id,
            step=session.current_step,
            action="mode_change",
            actor_kind="user",
            actor_id=actor_id,
            rationale=rationale or f"Mode changed: {old_mode} → {new_mode}",
        )
        await self._decision_repo.save(decision)

        return saved
