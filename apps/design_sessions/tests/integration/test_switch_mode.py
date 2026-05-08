"""Integration tests for SwitchModeUseCase. AC-01-M-006."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.design_sessions.application.use_cases.switch_mode import SwitchModeUseCase
from apps.design_sessions.domain.entities import DesignSession, PipelineStep, SessionMode, SessionStatus
from shared.domain.exceptions import ValidationError


pytestmark = pytest.mark.asyncio


def _make_auto_session(step: PipelineStep) -> DesignSession:
    s = DesignSession(
        project_id=uuid4(),
        started_by=uuid4(),
        mode=SessionMode.AUTO,
        status=SessionStatus.RESEARCHING,
        current_step=step,
    )
    s.tenant_id = "t1"
    s.workspace_id = uuid4()
    return s


def _mock_repos(session):
    session_repo = AsyncMock()
    decision_repo = AsyncMock()
    session_repo.get_by_id.side_effect = lambda sid: session
    session_repo.save.side_effect = lambda s: s
    decision_repo.save.side_effect = lambda d: d
    return session_repo, decision_repo


class TestSwitchModeUseCase:
    async def test_auto_to_guided_at_boundary_succeeds(self):
        # TREND_RESEARCH (step 5) is the only step in RESEARCHING state → boundary
        session = _make_auto_session(PipelineStep.TREND_RESEARCH)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = SwitchModeUseCase(session_repo, decision_repo)
            result = await uc.execute(
                session_id=session.id,
                new_mode="guided",
                actor_id=uuid4(),
            )

        assert result.mode == SessionMode.GUIDED

    async def test_auto_to_guided_mid_step_raises(self):
        # CONCEPT_GENERATION (step 6) is NOT the last step in CONCEPTING state
        session = _make_auto_session(PipelineStep.CONCEPT_GENERATION)
        session.status = SessionStatus.CONCEPTING
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = SwitchModeUseCase(session_repo, decision_repo)
            with pytest.raises(ValidationError):
                await uc.execute(
                    session_id=session.id,
                    new_mode="guided",
                    actor_id=uuid4(),
                )

    async def test_records_mode_change_decision(self):
        session = _make_auto_session(PipelineStep.TREND_RESEARCH)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = SwitchModeUseCase(session_repo, decision_repo)
            await uc.execute(session_id=session.id, new_mode="guided", actor_id=uuid4())

        decision_repo.save.assert_called_once()
        decision = decision_repo.save.call_args[0][0]
        assert decision.action == "mode_change"
