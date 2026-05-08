"""Base Django ORM models with timestamp and tenant scoping."""
from django.db import models

# @MX:ANCHOR: [AUTO] TenantScopedModel is the inheritance base for all workspace-scoped models
# @MX:REASON: fan_in >= 3; DesignSession, Conversation, UserSketchAsset and others inherit this


class TimestampedModel(models.Model):
    """Abstract base model with timestamp fields."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class TenantScopedModel(models.Model):
    """Abstract base model with tenant and workspace scoping.

    All concrete subclasses automatically get tenant-filtered queries via
    TenantAwareManager (objects) while retaining an unfiltered escape hatch
    via all_objects (for admin/migration paths only).

    REQ-01-TENANT-001: ORM-level auto-filtering enforced here.
    """

    tenant_id = models.CharField(max_length=255, db_index=True)
    workspace_id = models.UUIDField(db_index=True)

    # Auto-filtered manager (respects TenantContext)
    objects: models.Manager  # assigned below after import

    # Unfiltered escape hatch — use ONLY in admin/audit/migration contexts
    all_objects = models.Manager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant_id', 'workspace_id']),
        ]


# Lazy import to avoid circular imports at module load time
def _get_tenant_aware_manager():
    from shared.infrastructure.orm.managers import TenantAwareManager
    return TenantAwareManager()


# Apply TenantAwareManager as the default manager
TenantScopedModel.add_to_class('objects', _get_tenant_aware_manager())


class SoftDeleteModel(models.Model):
    """Abstract base model for soft delete (tombstone) pattern."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_deleted', '-created_at']),
        ]

    def soft_delete(self) -> None:
        """Mark the object as deleted instead of actually deleting."""
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def undelete(self) -> None:
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
