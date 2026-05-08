"""User asset Django ORM models.

Immutable sketch storage with versioning.
"""
from django.db import models
from django.core.exceptions import ValidationError
from shared.infrastructure.orm.base_model import TimestampedModel, TenantScopedModel


class UserSketchAssetManager(models.Manager):
    """Manager for user sketch asset queries."""

    def for_session(self, session_id):
        """Filter assets by session."""
        return self.filter(session_id=session_id)

    def latest_version(self):
        """Get latest version for each asset."""
        return self.order_by("parent_asset_id", "-version").distinct("parent_asset_id")


class UserSketchAsset(TenantScopedModel, TimestampedModel):
    """User sketch asset model with immutability guarantees.

    Original URI and SHA-256 never change - new versions create new records.
    """

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    uploader_id = models.UUIDField()
    original_uri = models.TextField()  # Immutable
    sha256 = models.CharField(max_length=64)  # Immutable
    mime_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField()
    version = models.IntegerField(default=1)
    parent_asset_id = models.UUIDField(null=True, blank=True, db_index=True)

    objects = UserSketchAssetManager()

    class Meta:
        db_table = "user_sketch_assets"
        verbose_name = "User Sketch Asset"
        verbose_name_plural = "User Sketch Assets"
        unique_together = [["session_id", "sha256", "version"]]
        indexes = [
            models.Index(fields=["session_id", "created_at"]),
            models.Index(fields=["uploader_id"]),
            models.Index(fields=["parent_asset_id", "version"]),
        ]

    def __str__(self) -> str:
        return f"Sketch {self.id} v{self.version}"

    def clean(self):
        """Validate immutability on update."""
        if self.pk:
            old_instance = UserSketchAsset.objects.get(pk=self.pk)

            # Enforce immutability
            if self.original_uri != old_instance.original_uri:
                raise ValidationError({"original_uri": "Cannot change original_uri after creation"})

            if self.sha256 != old_instance.sha256:
                raise ValidationError({"sha256": "Cannot change sha256 after creation"})

    def save(self, *args, **kwargs):
        """Override save to enforce immutability."""
        self.clean()
        super().save(*args, **kwargs)


class SketchAnalysisManager(models.Manager):
    """Manager for sketch analysis queries."""

    def for_sketch(self, sketch_id):
        """Filter analyses by sketch."""
        return self.filter(sketch_id=sketch_id)

    def hypotheses(self):
        """Get unconfirmed hypotheses."""
        return self.filter(status="hypothesis")

    def confirmed(self):
        """Get confirmed analyses."""
        return self.filter(status="confirmed")


class SketchAnalysis(TimestampedModel):
    """Sketch analysis model.

    AI-generated hypothesis about sketch content.
    """

    id = models.UUIDField(primary_key=True)
    sketch_id = models.UUIDField(unique=True, db_index=True)
    intent = models.TextField()
    form_notes = models.TextField()
    structure_notes = models.TextField()
    unclear_points = models.TextField(blank=True)
    keep_elements = models.TextField(blank=True)
    vary_elements = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("hypothesis", "Hypothesis"),
            ("confirmed", "Confirmed"),
            ("rejected", "Rejected"),
        ],
        default="hypothesis",
    )

    objects = SketchAnalysisManager()

    class Meta:
        db_table = "sketch_analyses"
        verbose_name = "Sketch Analysis"
        verbose_name_plural = "Sketch Analyses"
        indexes = [
            models.Index(fields=["sketch_id", "status"]),
        ]

    def __str__(self) -> str:
        return f"Analysis for sketch {self.sketch_id} ({self.status})"
