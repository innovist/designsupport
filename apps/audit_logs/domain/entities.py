"""Audit log domain entities.

Pure Python domain entities with no Django ORM dependency.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
from uuid import UUID
from typing import Optional, Dict, Any


class ActionType:
    """Audit log action type value object."""

    USER_ACTION = "user_action"
    ADMIN_ACTION = "admin_action"
    AI_CALL = "ai_call"


# @MX:NOTE: [AUTO] Immutable audit log - append-only write pattern for compliance
# @MX:REASON: Domain invariant - audit logs must never be modified after creation
@dataclass
class AuditLog:
    """Audit log entity for tracking all system actions.

    Immutable record - once written, never updated or deleted.
    """

    actor_id: UUID
    tenant_id: str
    workspace_id: Optional[UUID]
    action_type: str
    target_type: str
    target_id: str
    payload_digest: str
    created_at: datetime

    def __init__(
        self,
        actor_id: UUID,
        tenant_id: str,
        action_type: str,
        target_type: str,
        target_id: str,
        payload_digest: str,
        workspace_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize an audit log entry.

        Args:
            actor_id: User who performed the action
            tenant_id: Tenant ID
            action_type: Type of action (user_action, admin_action, ai_call)
            target_type: Type of target entity
            target_id: ID of target entity
            payload_digest: Hash of action payload
            workspace_id: Optional workspace ID
            created_at: Timestamp
        """
        self.actor_id = actor_id
        self.tenant_id = tenant_id
        self.workspace_id = workspace_id
        self.action_type = action_type
        self.target_type = target_type
        self.target_id = target_id
        self.payload_digest = payload_digest
        self.created_at = created_at or _utcnow()
