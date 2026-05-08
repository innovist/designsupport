"""Audit log Django ORM models.

Immutable audit trail for compliance and security.
"""
from django.db import models
from shared.infrastructure.orm.base_model import TimestampedModel


class AuditLog(TimestampedModel):
    """Immutable audit log model.

    Tracks all user actions, admin actions, and AI calls.
    Records are never updated or deleted, only inserted.
    """

    id = models.BigAutoField(primary_key=True)
    actor_id = models.UUIDField(db_index=True, null=True, blank=True)
    tenant_id = models.CharField(max_length=255, db_index=True)
    workspace_id = models.UUIDField(null=True, blank=True, db_index=True)
    action_type = models.CharField(
        max_length=100,  # Extended: supports dot-notation e.g. "design_session.create"
        db_index=True,
    )
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=255)
    payload_digest = models.CharField(max_length=64)  # SHA-256 hash

    class Meta(TimestampedModel.Meta):
        abstract = False
        db_table = "audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["tenant_id", "created_at"]),
            models.Index(fields=["actor_id", "action_type"]),
            models.Index(fields=["workspace_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action_type} on {self.target_type}:{self.target_id} by {self.actor_id}"

    def save(self, *args, **kwargs):
        """Override save to prevent updates.

        Raises:
            ValueError: If trying to update an existing log entry
        """
        if self.pk is not None:
            raise ValueError("Audit log entries cannot be updated")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion.

        Raises:
            ValueError: Audit logs cannot be deleted
        """
        raise ValueError("Audit log entries cannot be deleted")
