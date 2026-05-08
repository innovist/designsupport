"""Django ORM repository for AuditLog.

REQ-01-AUDIT-003: bulk_create with ignore_conflicts=False so DB errors propagate.
"""
from typing import List, Tuple

from apps.audit_logs.application.dtos import AuditLogEntryDTO
from apps.audit_logs.application.ports import (
    AuditLogRepositoryPort,
    AuditQueryFilters,
    AuditQueryPagination,
)
from apps.audit_logs.infrastructure.orm.models import AuditLog
from shared.domain.exceptions import OperationError


class DjangoAuditLogRepository(AuditLogRepositoryPort):
    """Django ORM implementation of AuditLogRepositoryPort.

    append() uses bulk_create([entry], ignore_conflicts=False) so any DB
    integrity error propagates to the caller's atomic() block.
    """

    def append(self, entry: AuditLogEntryDTO) -> None:
        """Persist a single audit log entry.

        Must be called inside the same transaction as the use case.
        Uses bulk_create with ignore_conflicts=False so errors propagate.

        Args:
            entry: DTO to persist

        Raises:
            OperationError: Wraps any Django DB exception
        """
        try:
            # Use all_objects manager — audit log is NOT tenant-filtered
            AuditLog.objects.bulk_create(
                [
                    AuditLog(
                        actor_id=entry.actor_id,
                        tenant_id=entry.tenant_id or "",
                        workspace_id=entry.workspace_id,
                        action_type=entry.action_type[:100],  # guard length
                        target_type=entry.target_type,
                        target_id=entry.target_id,
                        payload_digest=entry.payload_digest,
                    )
                ],
                ignore_conflicts=False,
            )
        except Exception as exc:
            raise OperationError(
                operation="audit_log.append",
                reason=str(exc),
            ) from exc

    def query(
        self,
        filters: AuditQueryFilters,
        pagination: AuditQueryPagination,
    ) -> Tuple[List[AuditLogEntryDTO], int]:
        """Query audit logs with filters and pagination.

        Uses all_objects so no tenant auto-filter is applied —
        caller is responsible for scoping via filters.

        Args:
            filters: Field-level filters
            pagination: Offset/limit

        Returns:
            Tuple of (entries, total_count)
        """
        qs = AuditLog.objects.all().order_by("-created_at")

        if filters.tenant_id:
            qs = qs.filter(tenant_id=filters.tenant_id)
        if filters.workspace_id:
            qs = qs.filter(workspace_id=filters.workspace_id)
        if filters.actor_id:
            qs = qs.filter(actor_id=filters.actor_id)
        if filters.action_type:
            qs = qs.filter(action_type=filters.action_type)
        if filters.target_type:
            qs = qs.filter(target_type=filters.target_type)

        total = qs.count()
        entries = [
            self._to_dto(row)
            for row in qs[pagination.offset : pagination.offset + pagination.limit]
        ]
        return entries, total

    @staticmethod
    def _to_dto(model: AuditLog) -> AuditLogEntryDTO:
        return AuditLogEntryDTO(
            actor_id=model.actor_id,
            tenant_id=model.tenant_id,
            workspace_id=model.workspace_id,
            action_type=model.action_type,
            target_type=model.target_type,
            target_id=model.target_id,
            payload_digest=model.payload_digest,
            created_at=model.created_at,
        )
