"""Integration tests for RecordDecisionUseCase. REQ-01-ORCH-006."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.design_sessions.application.use_cases.record_decision import RecordDecisionUseCase
from apps.design_sessions.domain.entities import PipelineStep
from shared.domain.exceptions import ValidationError


pytestmark = pytest.mark.asyncio


class TestRecordDecisionUseCase:
    def _mock_decision_repo(self):
        repo = AsyncMock()
        repo.save.side_effect = lambda d: d
        return repo

    async def test_user_decision_persisted(self):
        repo = self._mock_decision_repo()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RecordDecisionUseCase(repo)
            decision = await uc.execute(
                session_id=uuid4(),
                step=5,
                action="approved_concept",
                actor_kind="user",
                actor_id=uuid4(),
                rationale="Looks good",
            )

        assert decision.actor_kind == "user"
        assert decision.step == PipelineStep.TREND_RESEARCH

    async def test_auto_decision_persisted(self):
        repo = self._mock_decision_repo()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RecordDecisionUseCase(repo)
            decision = await uc.execute(
                session_id=uuid4(),
                step=6,
                action="auto_progressed",
                actor_kind="auto",
                actor_id=uuid4(),
                rationale="Auto-progression",
            )

        assert decision.actor_kind == "auto"

    async def test_invalid_actor_kind_raises(self):
        repo = self._mock_decision_repo()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = RecordDecisionUseCase(repo)
            with pytest.raises(ValidationError):
                await uc.execute(
                    session_id=uuid4(),
                    step=5,
                    action="test",
                    actor_kind="invalid",
                    actor_id=uuid4(),
                    rationale="test",
                )
