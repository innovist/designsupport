"""Workspace domain entities.

Pure Python domain entities with no Django ORM dependency.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from enum import Enum


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TenantPlan(Enum):
    """Tenant subscription plan."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class Tenant:
    """Tenant aggregate root entity.

    Represents a multi-tenant organization with subscription plan.
    """

    id: str
    name: str
    plan: TenantPlan
    is_active: bool
    created_at: datetime

    def __init__(
        self,
        name: str,
        plan: TenantPlan = TenantPlan.FREE,
        is_active: bool = True,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize a new Tenant.

        Args:
            name: Tenant organization name
            plan: Subscription plan
            is_active: Active status
            id: Tenant ID string (auto-generated if None)
            created_at: Creation timestamp
        """
        self.id = id or str(uuid4())
        self.name = name
        self.plan = plan
        self.is_active = is_active
        self.created_at = created_at or _utcnow()

    def upgrade_plan(self, new_plan: TenantPlan) -> None:
        """Upgrade tenant subscription plan.

        Args:
            new_plan: New plan to upgrade to
        """
        if self.plan == new_plan:
            return  # Already on this plan
        self.plan = new_plan

    def deactivate(self) -> None:
        """Deactivate tenant."""
        if not self.is_active:
            return
        self.is_active = False


@dataclass
class Workspace:
    """Workspace aggregate root entity.

    Represents a workspace within a tenant for design project organization.
    """

    id: UUID
    tenant_id: str
    name: str
    description: Optional[str]
    is_active: bool

    def __init__(
        self,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        id: Optional[UUID] = None,
    ):
        """Initialize a new Workspace.

        Args:
            tenant_id: Tenant ID string
            name: Workspace name
            description: Optional description
            is_active: Active status
            id: Workspace UUID (auto-generated if None)
        """
        self.id = id or uuid4()
        self.tenant_id = tenant_id
        self.name = name
        self.description = description
        self.is_active = is_active

    def deactivate(self) -> None:
        """Deactivate workspace."""
        if not self.is_active:
            return
        self.is_active = False


@dataclass
class Membership:
    """Membership entity representing user-workspace association.

    Link entity between User and Workspace with role information.
    """

    user_id: UUID
    workspace_id: UUID
    role: str  # admin, lead, designer, viewer
    joined_at: datetime

    def __init__(
        self,
        user_id: UUID,
        workspace_id: UUID,
        role: str = "viewer",
        joined_at: Optional[datetime] = None,
    ):
        """Initialize a new Membership.

        Args:
            user_id: User UUID
            workspace_id: Workspace UUID
            role: Role string (default: viewer)
            joined_at: Join timestamp
        """
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.role = role
        self.joined_at = joined_at or _utcnow()

    def update_role(self, new_role: str) -> None:
        """Update member role.

        Args:
            new_role: New role string
        """
        if self.role == new_role:
            return
        self.role = new_role
