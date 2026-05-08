"""Application ports for audit_logs module.

REQ-01-AUDIT-001..003: Define interfaces for audit log persistence.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from .dtos import AuditLogEntryDTO


@dataclass
class AuditQueryFilters:
    """Filters for querying audit logs."""

    tenant_id: Optional[str] = None
    workspace_id: Optional[UUID] = None
    actor_id: Optional[UUID] = None
    action_type: Optional[str] = None
    target_type: Optional[str] = None


@dataclass
class AuditQueryPagination:
    """Pagination parameters for audit log queries."""

    offset: int = 0
    limit: int = 50


class AuditLogRepositoryPort(ABC):
    """Repository port for AuditLog persistence.

    REQ-01-AUDIT-003: append failures must propagate to caller for rollback.
    """

    # @MX:ANCHOR: [AUTO] append is called by the @audit decorator for every audited use case
    # @MX:REASON: fan_in >= 3; decorator, query use case, and admin path all use this port
    @abstractmethod
    def append(self, entry: AuditLogEntryDTO) -> None:
        """Append a single audit log entry.

        MUST be called inside the same DB transaction as the use case.
        If this raises, the caller's transaction is rolled back.

        Args:
            entry: Audit log DTO to persist

        Raises:
            OperationError: On DB write failure (propagates for rollback)
        """
        ...

    @abstractmethod
    def query(
        self,
        filters: AuditQueryFilters,
        pagination: AuditQueryPagination,
    ) -> tuple[List["AuditLogEntryDTO"], int]:
        """Query audit logs with filters and pagination.

        Args:
            filters: Field-level filters
            pagination: Offset/limit pagination

        Returns:
            Tuple of (list of entries, total count matching filters)
        """
        ...
