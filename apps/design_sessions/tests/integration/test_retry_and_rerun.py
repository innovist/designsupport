"""Integration tests for RetryStepUseCase and RerunFromStepUseCase.

AC-01-R-007: rerun_from_step preserves prior artifacts; version bumps.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.design_sessions.application.use_cases.retry_step import RetryStepUseCase
from apps.design_sessions.application.use_cases.rerun_from_step import RerunFromStepUseCase
from apps.design_sessions.domain.entities import DesignSession, PipelineStep, SessionMode, SessionStatus
from shared.domain.exceptions import NotFoundError, StateTransitionError, ValidationError


pytestmark = pytest.mark.asyncio


def _make_session(status: SessionStatus, step: PipelineStep = PipelineStep.PURPOSE_INPUT, version: int = 1):
    s = DesignSession(
        project_id=uuid4(),
        started_by=uuid4(),
        status=status,
        current_step=step,
        version=version,
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


class TestRetryStepUseCase:
    async def test_failed_session_transitions_to_queued(self):
        session = _make_session(SessionStatus.FAILED)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RetryStepUseCase(session_repo, decision_repo)
            result = await uc.execute(session_id=session.id, actor_id=uuid4())

        assert result.status == SessionStatus.QUEUED

    async def test_non_failed_session_raises_state_transition_error(self):
        session = _make_session(SessionStatus.RESEARCHING)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RetryStepUseCase(session_repo, decision_repo)
            with pytest.raises(StateTransitionError):
                await uc.execute(session_id=session.id, actor_id=uuid4())

    async def test_retry_records_decision_log(self):
        session = _make_session(SessionStatus.FAILED)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RetryStepUseCase(session_repo, decision_repo)
            await uc.execute(session_id=session.id, actor_id=uuid4())

        decision_repo.save.assert_called_once()
        decision = decision_repo.save.call_args[0][0]
        assert decision.action == "retry"


class TestRerunFromStepUseCase:
    async def test_bumps_version(self):
        session = _make_session(SessionStatus.FAILED, version=1)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RerunFromStepUseCase(session_repo, decision_repo)
            result = await uc.execute(
                session_id=session.id,
                from_step=5,  # TREND_RESEARCH → RESEARCHING
                actor_id=uuid4(),
            )

        assert result.version == 2

    async def test_sets_correct_step_and_status(self):
        session = _make_session(SessionStatus.FAILED)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RerunFromStepUseCase(session_repo, decision_repo)
            result = await uc.execute(
                session_id=session.id,
                from_step=5,  # TREND_RESEARCH
                actor_id=uuid4(),
            )

        assert result.current_step == PipelineStep.TREND_RESEARCH
        assert result.status == SessionStatus.RESEARCHING

    async def test_invalid_step_raises_validation_error(self):
        session = _make_session(SessionStatus.FAILED)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RerunFromStepUseCase(session_repo, decision_repo)
            with pytest.raises(ValidationError):
                await uc.execute(
                    session_id=session.id,
                    from_step=99,
                    actor_id=uuid4(),
                )
