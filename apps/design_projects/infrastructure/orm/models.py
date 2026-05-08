"""Design project Django ORM models.

Project organization with domain classification.
"""
from django.db import models
from shared.infrastructure.orm.base_model import TimestampedModel, TenantScopedModel, SoftDeleteModel


class DesignProjectManager(models.Manager):
    """Manager for design project queries."""

    def for_workspace(self, workspace_id):
        """Filter projects by workspace."""
        return self.filter(workspace_id=workspace_id)

    def active(self):
        """Get active projects."""
        return self.filter(status="active")

    def by_domain(self, domain):
        """Filter projects by design domain."""
        return self.filter(domain=domain)


class DesignProject(TenantScopedModel, TimestampedModel, SoftDeleteModel):
    """Design project model.

    Organizes design sessions within workspaces.
    """

    id = models.UUIDField(primary_key=True)
    workspace_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=255)
    domain = models.CharField(
        max_length=20,
        choices=[
            ("industrial", "Industrial Design"),
            ("fashion", "Fashion Design"),
            ("visual", "Visual Design"),
            ("advertising", "Advertising Design"),
        ],
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("archived", "Archived"),
            ("deleted", "Deleted"),
        ],
        default="active",
        db_index=True,
    )
    owner_id = models.UUIDField(db_index=True)

    objects = DesignProjectManager()

    class Meta:
        db_table = "design_projects"
        verbose_name = "Design Project"
        verbose_name_plural = "Design Projects"
        indexes = [
            models.Index(fields=["workspace_id", "status"]),
            models.Index(fields=["owner_id"]),
            models.Index(fields=["domain"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.domain})"
