"""Account domain entities.

Pure Python domain entities with no Django ORM dependency.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# @MX:ANCHOR: [AUTO] User aggregate root - core domain entity
# @MX:REASON: High fan_in - used by all account use cases and repositories
@dataclass
class User:
    """User aggregate root entity."""

    id: UUID
    email: str
    password_hash: str
    display_name: str
    default_workspace_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        email: str,
        password_hash: str,
        display_name: str,
        default_workspace_id: Optional[UUID] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id or uuid4()
        self.email = email
        self.password_hash = password_hash
        self.display_name = display_name
        self.default_workspace_id = default_workspace_id
        self.is_active = is_active
        self.created_at = created_at or _utcnow()
        self.updated_at = updated_at or _utcnow()

    # @MX:ANCHOR: [AUTO] Workspace default setting for multi-tenant context
    # @MX:REASON: High fan_in - called by registration, profile update, workspace switch
    def set_default_workspace(self, workspace_id: UUID) -> None:
        """Set the default workspace."""
        self.default_workspace_id = workspace_id
        self.updated_at = _utcnow()

    def deactivate(self) -> None:
        """Deactivate the user account."""
        if not self.is_active:
            return
        self.is_active = False
        self.updated_at = _utcnow()

    def activate(self) -> None:
        """Activate the user account."""
        if self.is_active:
            return
        self.is_active = True
        self.updated_at = _utcnow()
