"""Workspace domain events.

Events raised during workspace aggregate operations.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
from uuid import UUID
from typing import Optional


@dataclass
class WorkspaceCreated:
    """Event raised when a new workspace is created."""

    workspace_id: UUID
    tenant_id: str
    name: str
    created_by: UUID
    created_at: datetime

    def __init__(
        self,
        workspace_id: UUID,
        tenant_id: str,
        name: str,
        created_by: UUID,
        created_at: Optional[datetime] = None,
    ):
        """Initialize workspace created event."""
        self.workspace_id = workspace_id
        self.tenant_id = tenant_id
        self.name = name
        self.created_by = created_by
        self.created_at = created_at or _utcnow()


@dataclass
class MemberAdded:
    """Event raised when a member is added to a workspace."""

    workspace_id: UUID
    tenant_id: str
    user_id: UUID
    role: str
    added_by: UUID
    added_at: datetime

    def __init__(
        self,
        workspace_id: UUID,
        tenant_id: str,
        user_id: UUID,
        role: str,
        added_by: UUID,
        added_at: Optional[datetime] = None,
    ):
        """Initialize member added event."""
        self.workspace_id = workspace_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
        self.added_by = added_by
        self.added_at = added_at or _utcnow()


@dataclass
class MemberRoleChanged:
    """Event raised when a member's role is changed."""

    workspace_id: UUID
    tenant_id: str
    user_id: UUID
    old_role: str
    new_role: str
    changed_by: UUID
    changed_at: datetime

    def __init__(
        self,
        workspace_id: UUID,
        tenant_id: str,
        user_id: UUID,
        old_role: str,
        new_role: str,
        changed_by: UUID,
        changed_at: Optional[datetime] = None,
    ):
        """Initialize member role changed event."""
        self.workspace_id = workspace_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.old_role = old_role
        self.new_role = new_role
        self.changed_by = changed_by
        self.changed_at = changed_at or _utcnow()
