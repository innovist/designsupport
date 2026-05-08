"""References Django ORM models.

Implements ReferenceAsset, ReferenceAnalysis, ReferenceQuery, ImageProviderQuota.
Includes proper indexes and constraints per SPEC-02 requirements.
"""
from django.db import models
from shared.infrastructure.orm.base_model import TimestampedModel


class ReferenceAsset(TimestampedModel):
    """Reference asset ORM model.

    Represents a reference material (image, document, web page, internal asset).
    Enforces thumbnail constraint (max 1024px) per SPEC-02 REQ-02-REF-010.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # References
    session_id = models.UUIDField(db_index=True)

    # Asset classification
    kind = models.CharField(
        max_length=20,
        db_index=True,
        choices=[
            ("image", "Image"),
            ("document", "Document"),
            ("internal", "Internal"),
            ("web_page", "Web Page"),
        ],
    )
    provider = models.CharField(max_length=100, db_index=True)
    tier = models.IntegerField()  # 1, 2, or 3

    # Thumbnail - max 1024px constraint enforced
    thumbnail_uri = models.CharField(max_length=2048)
    thumbnail_max_edge_px = models.IntegerField(default=1024)

    # Asset metadata
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=255, null=True, blank=True)
    source_url = models.URLField(max_length=2048, null=True, blank=True)
    external_url = models.URLField(max_length=2048, null=True, blank=True)

    # Timestamps
    collected_at = models.DateTimeField(db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # License and attribution
    license_id = models.CharField(max_length=100)  # SPDX or provider ID
    license_risk = models.CharField(
        max_length=20,
        db_index=True,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("unknown", "Unknown"),
        ],
    )
    attribution_text = models.TextField()

    # Classification and analysis
    domain_tags = models.JSONField(default=list)
    relevance_reason = models.TextField(null=True, blank=True)
    abstractable_elements = models.JSONField(default=list)
    copy_risk = models.CharField(max_length=20)

    class Meta:
        db_table = "references_asset"
        verbose_name = "Reference Asset"
        verbose_name_plural = "Reference Assets"
        indexes = [
            models.Index(fields=["session_id", "kind"]),
            models.Index(fields=["provider", "tier"]),
            models.Index(fields=["license_risk"]),
            models.Index(fields=["-collected_at"]),
        ]

    def clean(self):
        """Validate thumbnail constraint before save."""
        from django.core.exceptions import ValidationError

        if self.thumbnail_max_edge_px > 1024:
            raise ValidationError(
                f"Thumbnail max edge must be <= 1024px, got {self.thumbnail_max_edge_px}"
            )


class ReferenceAnalysis(TimestampedModel):
    """Reference analysis ORM model.

    Structured analysis of a reference asset.
    Extracts form, structure, material, and symbol analysis.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # References
    asset_id = models.UUIDField(db_index=True, unique=True)

    # Analysis scores
    relevance = models.FloatField()  # 0.0 to 1.0

    # Analysis content
    form_grammar = models.TextField(null=True, blank=True)
    structure_grammar = models.TextField(null=True, blank=True)
    material_note = models.TextField(null=True, blank=True)
    symbol_note = models.TextField(null=True, blank=True)

    # Risk assessment
    copy_risk = models.CharField(max_length=20)

    class Meta:
        db_table = "references_analysis"
        verbose_name = "Reference Analysis"
        verbose_name_plural = "Reference Analyses"
        indexes = [
            models.Index(fields=["asset_id"]),
        ]


class ReferenceQuery(TimestampedModel):
    """Reference query ORM model.

    Tracks search queries for analytics and optimization.
    Supports 6 query types per SPEC-02 REQ-02-REF-001.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # References
    session_id = models.UUIDField(db_index=True)
    requested_by = models.UUIDField(db_index=True)

    # Query information
    query_kind = models.CharField(
        max_length=20,
        db_index=True,
        choices=[
            ("keyword", "Keyword"),
            ("image", "Image"),
            ("sketch", "Sketch"),
            ("document", "Document"),
            ("internal", "Internal"),
            ("expanded", "Expanded"),
        ],
    )
    payload = models.TextField()  # JSON string

    class Meta:
        db_table = "references_query"
        verbose_name = "Reference Query"
        verbose_name_plural = "Reference Queries"
        indexes = [
            models.Index(fields=["session_id", "query_kind"]),
            models.Index(fields=["requested_by"]),
            models.Index(fields=["-created_at"]),
        ]


class ImageProviderQuota(TimestampedModel):
    """Image provider quota ORM model.

    Tracks API usage and rate limits per provider.
    Enables round-robin when limits are exceeded per SPEC-02 REQ-02-REF-016.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # Provider identification
    provider = models.CharField(max_length=100, unique=True, db_index=True)

    # Quota limits
    daily_limit = models.IntegerField()
    used_today = models.IntegerField(default=0)
    reset_at = models.DateTimeField(db_index=True)

    # Status
    active = models.BooleanField(default=True, db_index=True)
    last_error_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "references_image_provider_quota"
        verbose_name = "Image Provider Quota"
        verbose_name_plural = "Image Provider Quotas"
        indexes = [
            models.Index(fields=["provider", "active"]),
            models.Index(fields=["reset_at"]),
        ]


ReferenceAssetModel = ReferenceAsset
ReferenceAnalysisModel = ReferenceAnalysis
ReferenceQueryModel = ReferenceQuery
ImageProviderQuotaModel = ImageProviderQuota
