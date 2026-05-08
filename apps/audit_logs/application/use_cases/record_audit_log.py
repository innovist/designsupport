"""Record audit log use case.

REQ-01-AUDIT-001: Non-destructive append of audit entries.
REQ-01-AUDIT-003: Failure propagates to caller for transaction rollback.
"""
from apps.audit_logs.application.dtos import AuditLogEntryDTO
from apps.audit_logs.application.ports import AuditLogRepositoryPort


class RecordAuditLogUseCase:
    """Idempotent append of a single audit log entry.

    This use case is called by the @audit decorator INSIDE the same DB
    transaction as the use case being audited.  If append() raises, the
    exception propagates upward so Django's atomic() can rollback.
    """

    def __init__(self, repository: AuditLogRepositoryPort) -> None:
        self._repository = repository

    def execute(self, entry: AuditLogEntryDTO) -> None:
        """Append entry to the audit log.

        Args:
            entry: Populated AuditLogEntryDTO

        Raises:
            OperationError: On repository failure (triggers caller rollback)
        """
        self._repository.append(entry)
