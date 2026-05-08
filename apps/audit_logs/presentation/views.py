"""Admin API views for audit_logs module.

Admin list endpoint at /admin/audit-logs/ restricted to Tenant Admin role.
AC-01-A-005: Paginated audit log listing.
"""
from django.http import HttpRequest
from rest_framework.response import Response

from apps.audit_logs.application.ports import AuditQueryFilters, AuditQueryPagination
from apps.audit_logs.application.use_cases.query_audit_logs import QueryAuditLogsUseCase
from apps.audit_logs.infrastructure.repositories.audit_log_repository import (
    DjangoAuditLogRepository,
)
from shared.presentation.base_views import AdminOnlyAPIView
from shared.presentation.error_handlers import custom_exception_handler


def _to_response(payload: dict) -> Response:
    """Convert error handler dict payload to a DRF Response."""
    http_status = payload.pop("status", 500)
    return Response(payload, status=http_status)


# @MX:ANCHOR: [AUTO] Admin audit log query endpoint - compliance reporting
# @MX:REASON: High fan_in - used by admin console, compliance reports, investigations
class AuditLogListView(AdminOnlyAPIView):
    """List audit logs for admin users.

    GET /admin/audit-logs/
    Restricted to Tenant Admin role.
    """

    def get(self, request: HttpRequest) -> Response:
        """List audit log entries with optional filtering.

        Query parameters:
            workspace_id: Filter by workspace UUID
            actor_id: Filter by actor UUID
            action_type: Filter by action type string
            target_type: Filter by target type string
            offset: Pagination offset (default 0)
            limit: Page size (default 50, max 200)
        """
        try:
            use_case = QueryAuditLogsUseCase(repository=DjangoAuditLogRepository())

            filters = AuditQueryFilters(
                workspace_id=request.GET.get("workspace_id") or None,
                actor_id=request.GET.get("actor_id") or None,
                action_type=request.GET.get("action_type") or None,
                target_type=request.GET.get("target_type") or None,
            )
            offset = int(request.GET.get("offset", 0))
            limit = min(int(request.GET.get("limit", 50)), 200)
            pagination = AuditQueryPagination(offset=offset, limit=limit)

            tenant_id = getattr(request, "tenant_id", "")
            is_superuser = request.user.is_superuser

            entries, total = use_case.execute(
                requesting_tenant_id=tenant_id,
                is_superuser=is_superuser,
                filters=filters,
                pagination=pagination,
            )

            results = [
                {
                    "actor_id": str(e.actor_id) if e.actor_id else None,
                    "tenant_id": e.tenant_id,
                    "workspace_id": str(e.workspace_id) if e.workspace_id else None,
                    "action_type": e.action_type,
                    "target_type": e.target_type,
                    "target_id": e.target_id,
                    "payload_digest": e.payload_digest,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in entries
            ]

            return Response(
                {
                    "results": results,
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                }
            )
        except Exception as exc:
            return _to_response(custom_exception_handler(exc, {"view": self}))
