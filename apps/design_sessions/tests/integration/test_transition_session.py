"""Integration tests for TransitionSessionUseCase.

Invalid transition rejected; valid transition persisted; INV-01-04 covered.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.design_sessions.application.use_cases.transition_session import TransitionSessionUseCase
from apps.design_sessions.domain.entities import DesignSession, PipelineStep, SessionMode, SessionStatus
from shared.domain.exceptions import NotFoundError, StateTransitionError


pytestmark = pytest.mark.asyncio


def _make_session(status: SessionStatus) -> DesignSession:
    s = DesignSession(
        project_id=uuid4(),
        started_by=uuid4(),
        status=status,
        current_step=PipelineStep.PURPOSE_INPUT,
    )
    s.tenant_id = "t1"
    s.workspace_id = uuid4()
    return s


def _mock_repos(session=None):
    session_repo = AsyncMock()
    decision_repo = AsyncMock()

    async def get_by_id(sid):
        return session

    async def save(s):
        return s

    async def save_decision(d):
        return d

    session_repo.get_by_id.side_effect = get_by_id
    session_repo.save.side_effect = save
    decision_repo.save.side_effect = save_decision
    return session_repo, decision_repo


class TestTransitionSessionUseCase:
    async def test_valid_transition_succeeds(self):
        session = _make_session(SessionStatus.QUEUED)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = TransitionSessionUseCase(session_repo, decision_repo)
            result = await uc.execute(
                session_id=session.id,
                target_state="researching",
                actor_kind="auto",
                actor_id=uuid4(),
                rationale="Starting research",
            )

        assert result.status == SessionStatus.RESEARCHING

    async def test_invalid_transition_raises_state_transition_error(self):
        session = _make_session(SessionStatus.QUEUED)
        session_repo, decision_repo = _mock_repos(session)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = TransitionSessionUseCase(session_repo, decision_repo)
            with pytest.raises(StateTransitionError):
                await uc.execute(
                    session_id=session.id,
                    target_state="review_ready",  # cannot skip states
                    actor_kind="user",
                    actor_id=uuid4(),
                    rationale="skip attempt",
                )

    async def test_session_not_found_raises_not_found_error(self):
        session_repo, decision_repo = _mock_repos(None)

        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = TransitionSessionUseCase(session_repo, decision_repo)
            with pytest.raises(NotFoundError):
                await uc.execute(
                    session_id=uuid4(),
                    target_state="researching",
                    actor_kind="user",
                    actor_id=uuid4(),
                    rationale="test",
                )
