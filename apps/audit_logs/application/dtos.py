"""DTOs for audit_logs application layer.

REQ-01-AUDIT-002: AuditLogEntryDTO captures all required audit fields.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AuditLogEntryDTO:
    """Data transfer object for a single audit log entry.

    payload_digest is SHA-256 of canonicalized JSON of the use-case input
    (passwords, secrets, and tokens are redacted before hashing).
    Raw payload is NEVER stored.
    """

    action_type: str
    target_type: str
    target_id: str
    payload_digest: str
    actor_id: Optional[UUID] = None       # None for anonymous/system flows
    tenant_id: Optional[str] = None
    workspace_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=_utcnow)
