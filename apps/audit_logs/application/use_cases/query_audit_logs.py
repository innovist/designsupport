"""Query audit logs use case.

Admin-only read with tenant scoping for non-superusers.
AC-01-A-005: Pagination via shared/presentation/pagination.py.
"""
from typing import List, Tuple
from uuid import UUID

from apps.audit_logs.application.dtos import AuditLogEntryDTO
from apps.audit_logs.application.ports import (
    AuditLogRepositoryPort,
    AuditQueryFilters,
    AuditQueryPagination,
)
from shared.domain.exceptions import PermissionDeniedError


class QueryAuditLogsUseCase:
    """Query audit logs with tenant scoping.

    Non-superusers are restricted to their own tenant.
    Superusers can query across tenants by passing tenant_id=None.
    """

    def __init__(self, repository: AuditLogRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        requesting_tenant_id: str,
        is_superuser: bool,
        filters: AuditQueryFilters,
        pagination: AuditQueryPagination,
    ) -> Tuple[List[AuditLogEntryDTO], int]:
        """Execute audit log query with access control.

        Args:
            requesting_tenant_id: Tenant ID of the requesting admin
            is_superuser: Whether the requester is a superuser
            filters: Query filters (tenant_id in filters overrides for superusers)
            pagination: Offset/limit pagination

        Returns:
            Tuple of (list of entries, total count)

        Raises:
            PermissionDeniedError: If non-superuser tries cross-tenant query
        """
        if not is_superuser:
            # Non-superusers always scoped to own tenant
            if filters.tenant_id and filters.tenant_id != requesting_tenant_id:
                raise PermissionDeniedError(
                    action="query_audit_logs",
                    resource=f"tenant:{filters.tenant_id}",
                )
            filters = AuditQueryFilters(
                tenant_id=requesting_tenant_id,
                workspace_id=filters.workspace_id,
                actor_id=filters.actor_id,
                action_type=filters.action_type,
                target_type=filters.target_type,
            )

        return self._repository.query(filters, pagination)
