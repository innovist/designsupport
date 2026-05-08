"""Integration tests for @audit decorator.

TDD: decorator records on success; skips failure unless allowlisted; inside atomic.
"""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from apps.audit_logs.application.dtos import AuditLogEntryDTO
from shared.application.decorators.audit import audit


pytestmark = pytest.mark.django_db


class TestAuditDecoratorSync:
    """Sync execute() path."""

    def _make_use_case(self, record_failures=False):
        @audit(
            "test.action",
            target_type_extractor=lambda **kw: "TestModel",
            target_id_extractor=lambda **kw: "test-id",
            record_failures=record_failures,
        )
        class FakeUseCase:
            def execute(self, value: str) -> str:
                return f"result:{value}"

        return FakeUseCase()

    def _make_failing_use_case(self, record_failures=False):
        @audit(
            "test.failing",
            target_type_extractor=lambda **kw: "TestModel",
            record_failures=record_failures,
        )
        class FailingUseCase:
            def execute(self, value: str) -> str:
                raise ValueError("intentional failure")

        return FailingUseCase()

    @patch("shared.application.decorators.audit._get_repository")
    @patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get")
    def test_records_on_success(self, mock_context, mock_repo_factory):
        mock_repo = MagicMock()
        mock_repo_factory.return_value = mock_repo
        mock_context.return_value = ("tenant-1", uuid4(), uuid4())

        uc = self._make_use_case()
        result = uc.execute(value="hello")

        assert result == "result:hello"
        mock_repo.append.assert_called_once()
        entry: AuditLogEntryDTO = mock_repo.append.call_args[0][0]
        assert entry.action_type == "test.action"
        assert entry.target_type == "TestModel"
        assert entry.target_id == "test-id"

    @patch("shared.application.decorators.audit._get_repository")
    @patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get")
    def test_no_record_on_failure_by_default(self, mock_context, mock_repo_factory):
        mock_repo = MagicMock()
        mock_repo_factory.return_value = mock_repo
        mock_context.return_value = ("tenant-1", uuid4(), uuid4())

        uc = self._make_failing_use_case(record_failures=False)
        with pytest.raises(ValueError):
            uc.execute(value="hello")

        # Success append not called
        mock_repo.append.assert_not_called()

    @patch("shared.application.decorators.audit._get_repository")
    @patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get")
    def test_records_failure_when_allowlisted(self, mock_context, mock_repo_factory):
        mock_repo = MagicMock()
        mock_repo_factory.return_value = mock_repo
        mock_context.return_value = ("tenant-1", uuid4(), uuid4())

        uc = self._make_failing_use_case(record_failures=True)
        with pytest.raises(ValueError):
            uc.execute(value="hello")

        # Failure entry recorded
        mock_repo.append.assert_called_once()
        entry: AuditLogEntryDTO = mock_repo.append.call_args[0][0]
        assert entry.action_type.startswith("failed:")

    @patch("shared.application.decorators.audit._get_repository")
    @patch("shared.infrastructure.tenant_middleware.middleware.TenantContext.get")
    def test_system_prefix_for_anonymous_actor(self, mock_context, mock_repo_factory):
        mock_repo = MagicMock()
        mock_repo_factory.return_value = mock_repo
        mock_context.return_value = (None, None, None)

        uc = self._make_use_case()
        uc.execute(value="hello")

        entry: AuditLogEntryDTO = mock_repo.append.call_args[0][0]
        assert entry.action_type.startswith("system:")
