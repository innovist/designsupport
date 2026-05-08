"""Integration tests: AC-01-O-004 — failed state with retry exhaustion."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.design_sessions.application.use_cases.transition_session import TransitionSessionUseCase
from apps.design_sessions.application.use_cases.retry_step import RetryStepUseCase
from apps.design_sessions.domain.entities import DesignSession, PipelineStep, SessionStatus
from shared.domain.exceptions import StateTransitionError


pytestmark = pytest.mark.asyncio


def _make_session(status: SessionStatus):
    s = DesignSession(
        project_id=uuid4(),
        started_by=uuid4(),
        status=status,
        current_step=PipelineStep.CONCEPT_GENERATION,
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


class TestFailedState:
    async def test_transition_to_failed(self):
        session = _make_session(SessionStatus.CONCEPTING)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = TransitionSessionUseCase(session_repo, decision_repo)
            result = await uc.execute(
                session_id=session.id,
                target_state="failed",
                actor_kind="auto",
                actor_id=uuid4(),
                rationale="Step failed due to timeout",
            )

        assert result.status == SessionStatus.FAILED

    async def test_retry_after_failure_transitions_to_queued(self):
        session = _make_session(SessionStatus.FAILED)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RetryStepUseCase(session_repo, decision_repo)
            result = await uc.execute(session_id=session.id, actor_id=uuid4())

        assert result.status == SessionStatus.QUEUED

    async def test_retry_from_non_failed_raises(self):
        session = _make_session(SessionStatus.CONCEPTING)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RetryStepUseCase(session_repo, decision_repo)
            with pytest.raises(StateTransitionError):
                await uc.execute(session_id=session.id, actor_id=uuid4())
