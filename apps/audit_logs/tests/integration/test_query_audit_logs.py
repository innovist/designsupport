"""Integration tests for QueryAuditLogsUseCase.

Admin sees own tenant only unless superuser.
"""
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from apps.audit_logs.application.dtos import AuditLogEntryDTO
from apps.audit_logs.application.ports import AuditQueryFilters, AuditQueryPagination
from apps.audit_logs.application.use_cases.query_audit_logs import QueryAuditLogsUseCase
from shared.domain.exceptions import PermissionDeniedError


class TestQueryAuditLogsUseCase:
    def _make_entry(self, tenant_id: str) -> AuditLogEntryDTO:
        return AuditLogEntryDTO(
            actor_id=uuid4(),
            tenant_id=tenant_id,
            workspace_id=uuid4(),
            action_type="test.action",
            target_type="Test",
            target_id="1",
            payload_digest="abc",
        )

    def _mock_repo(self, entries, total):
        repo = MagicMock()
        repo.query.return_value = (entries, total)
        return repo

    def test_non_superuser_scoped_to_own_tenant(self):
        entries = [self._make_entry("tenant-A")]
        repo = self._mock_repo(entries, 1)
        uc = QueryAuditLogsUseCase(repo)

        results, total = uc.execute(
            requesting_tenant_id="tenant-A",
            is_superuser=False,
            filters=AuditQueryFilters(),
            pagination=AuditQueryPagination(),
        )

        # Repo was called with tenant_id=tenant-A
        called_filters: AuditQueryFilters = repo.query.call_args[0][0]
        assert called_filters.tenant_id == "tenant-A"

    def test_non_superuser_cannot_cross_tenant(self):
        repo = self._mock_repo([], 0)
        uc = QueryAuditLogsUseCase(repo)

        with pytest.raises(PermissionDeniedError):
            uc.execute(
                requesting_tenant_id="tenant-A",
                is_superuser=False,
                filters=AuditQueryFilters(tenant_id="tenant-B"),
                pagination=AuditQueryPagination(),
            )

    def test_superuser_can_query_all_tenants(self):
        entries = [self._make_entry("tenant-X")]
        repo = self._mock_repo(entries, 1)
        uc = QueryAuditLogsUseCase(repo)

        results, total = uc.execute(
            requesting_tenant_id="tenant-A",
            is_superuser=True,
            filters=AuditQueryFilters(tenant_id="tenant-X"),
            pagination=AuditQueryPagination(),
        )
        assert total == 1
