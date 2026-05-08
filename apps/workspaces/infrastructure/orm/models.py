"""Workspace Django ORM models.

Implements Tenant, Workspace, and Membership models with multi-tenancy support.
"""
from django.db import models
from shared.infrastructure.orm.base_model import TimestampedModel, TenantScopedModel


class TenantManager(models.Manager):
    """Custom manager for tenant-scoped queries."""

    def get_active(self):
        """Get all active tenants."""
        return self.filter(is_active=True)

    def get_by_plan(self, plan):
        """Get tenants by subscription plan."""
        return self.filter(plan=plan, is_active=True)


class Tenant(TimestampedModel):
    """Tenant model representing an organization.

    Root entity for multi-tenancy. All workspaces belong to a tenant.
    """

    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255)
    plan = models.CharField(
        max_length=20,
        choices=[("free", "Free"), ("pro", "Pro"), ("enterprise", "Enterprise")],
        default="free",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    objects = TenantManager()

    class Meta:
        db_table = "workspaces_tenant"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["plan"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"


class WorkspaceManager(models.Manager):
    """Manager with automatic tenant filtering."""

    def for_tenant(self, tenant_id):
        """Filter workspaces by tenant_id."""
        return self.filter(tenant_id=tenant_id)

    def get_active(self):
        """Get all active workspaces."""
        return self.filter(is_active=True)


class Workspace(TenantScopedModel, TimestampedModel):
    """Workspace model for organizing design projects.

    Tenant-scoped entity: each workspace belongs to exactly one tenant.
    """

    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    objects = WorkspaceManager()

    class Meta:
        db_table = "workspaces_workspace"
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["workspace_id", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name


class MembershipManager(models.Manager):
    """Manager with automatic workspace filtering."""

    def for_workspace(self, workspace_id):
        """Filter memberships by workspace_id."""
        return self.filter(workspace_id=workspace_id)

    def for_user(self, user_id):
        """Filter memberships by user_id."""
        return self.filter(user_id=user_id)

    def for_tenant(self, tenant_id):
        """Filter memberships by tenant via workspace."""
        return self.filter(workspace__tenant_id=tenant_id)


class Membership(models.Model):
    """Membership model linking users to workspaces with roles.

    Represents many-to-many relationship between User and Workspace
    with additional role information.
    """

    id = models.BigAutoField(primary_key=True)
    user_id = models.UUIDField(db_index=True)
    workspace_id = models.UUIDField(db_index=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ("admin", "Admin"),
            ("lead", "Lead"),
            ("designer", "Designer"),
            ("viewer", "Viewer"),
        ],
        default="viewer",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    objects = MembershipManager()

    class Meta:
        db_table = "workspaces_membership"
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
        unique_together = [["user_id", "workspace_id"]]
        indexes = [
            models.Index(fields=["user_id", "workspace_id"]),
            models.Index(fields=["workspace_id", "role"]),
        ]

    def __str__(self) -> str:
        return f"User {self.user_id} -> Workspace {self.workspace_id} ({self.role})"


class GlobalManager(models.Manager):
    """Manager that automatically filters by tenant_id.

    Use this manager for models that need automatic tenant isolation.
    """

    def __init__(self, tenant_field="tenant_id"):
        """Initialize with tenant field name.

        Args:
            tenant_field: Name of the tenant ID field (default: tenant_id)
        """
        self.tenant_field = tenant_field
        super().__init__()

    def for_tenant(self, tenant_id):
        """Filter query by tenant_id.

        Args:
            tenant_id: Tenant ID to filter by

        Returns:
            QuerySet filtered by tenant
        """
        return self.filter(**{self.tenant_field: tenant_id})
