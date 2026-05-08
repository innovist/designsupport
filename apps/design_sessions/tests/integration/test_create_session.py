"""Integration tests for CreateSessionUseCase.

AC-01-S-002: clarifying_questions generated when brief is incomplete.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.design_sessions.application.use_cases.create_session import CreateSessionUseCase
from apps.design_sessions.domain.entities import SessionStatus
from shared.domain.exceptions import ValidationError


pytestmark = pytest.mark.asyncio


def _mock_repos():
    session_repo = AsyncMock()
    brief_repo = AsyncMock()
    decision_repo = AsyncMock()

    async def save_session(s):
        return s

    async def save_brief(b):
        return b

    async def save_decision(d):
        return d

    session_repo.save.side_effect = save_session
    brief_repo.save.side_effect = save_brief
    decision_repo.save.side_effect = save_decision
    return session_repo, brief_repo, decision_repo


class TestCreateSessionUseCase:
    async def test_creates_session_with_queued_status(self):
        session_repo, brief_repo, decision_repo = _mock_repos()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = CreateSessionUseCase(session_repo, brief_repo, decision_repo)
            session = await uc.execute(
                project_id=uuid4(),
                started_by=uuid4(),
                tenant_id="t1",
                workspace_id=uuid4(),
                mode="guided",
                purpose="Create a logo",
                audience="Designers",
                result_form="Logo SVG",
            )
        assert session.status == SessionStatus.QUEUED

    async def test_produces_clarifying_questions_for_empty_purpose(self):
        session_repo, brief_repo, decision_repo = _mock_repos()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = CreateSessionUseCase(session_repo, brief_repo, decision_repo)
            session = await uc.execute(
                project_id=uuid4(),
                started_by=uuid4(),
                tenant_id="t1",
                workspace_id=uuid4(),
                purpose="",        # empty
                audience="Designers",
                result_form="Logo",
            )

        brief = getattr(session, "brief", None)
        assert brief is not None
        fields = [q["field"] for q in brief.clarifying_questions]
        assert "purpose" in fields

    async def test_produces_clarifying_questions_for_all_empty(self):
        session_repo, brief_repo, decision_repo = _mock_repos()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = CreateSessionUseCase(session_repo, brief_repo, decision_repo)
            session = await uc.execute(
                project_id=uuid4(),
                started_by=uuid4(),
                tenant_id="t1",
                workspace_id=uuid4(),
            )

        brief = getattr(session, "brief", None)
        assert len(brief.clarifying_questions) == 3  # purpose, audience, result_form

    async def test_no_clarifying_questions_when_brief_complete(self):
        session_repo, brief_repo, decision_repo = _mock_repos()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = CreateSessionUseCase(session_repo, brief_repo, decision_repo)
            session = await uc.execute(
                project_id=uuid4(),
                started_by=uuid4(),
                tenant_id="t1",
                workspace_id=uuid4(),
                purpose="Redesign brand identity",
                audience="Young professionals",
                result_form="Brand guidelines document",
            )

        brief = getattr(session, "brief", None)
        assert brief.clarifying_questions == []

    async def test_invalid_mode_raises_validation_error(self):
        session_repo, brief_repo, decision_repo = _mock_repos()
        with patch("shared.application.decorators.audit._get_repository", return_value=MagicMock()), \
             patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get",
                   return_value=("t1", uuid4(), uuid4())):
            uc = CreateSessionUseCase(session_repo, brief_repo, decision_repo)
            with pytest.raises(ValidationError):
                await uc.execute(
                    project_id=uuid4(),
                    started_by=uuid4(),
                    tenant_id="t1",
                    workspace_id=uuid4(),
                    mode="invalid_mode",
                )
