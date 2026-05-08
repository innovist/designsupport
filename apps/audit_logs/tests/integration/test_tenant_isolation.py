"""Integration test: AC-01-T-001 — cross-tenant access attempt is audit-logged."""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from apps.audit_logs.application.dtos import AuditLogEntryDTO
from apps.audit_logs.application.ports import AuditQueryFilters, AuditQueryPagination
from apps.audit_logs.application.use_cases.query_audit_logs import QueryAuditLogsUseCase
from shared.domain.exceptions import PermissionDeniedError


class TestTenantIsolation:
    def test_cross_tenant_raises_permission_denied(self):
        """Non-superuser requesting another tenant's data gets PermissionDeniedError."""
        repo = MagicMock()
        uc = QueryAuditLogsUseCase(repo)

        with pytest.raises(PermissionDeniedError) as exc_info:
            uc.execute(
                requesting_tenant_id="tenant-A",
                is_superuser=False,
                filters=AuditQueryFilters(tenant_id="tenant-B"),
                pagination=AuditQueryPagination(),
            )

        assert "tenant-B" in str(exc_info.value)
        # Repository should NOT be called for unauthorized cross-tenant access
        repo.query.assert_not_called()
