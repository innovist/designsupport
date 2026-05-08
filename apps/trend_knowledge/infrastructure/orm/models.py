"""Trend Knowledge Django ORM models.

Implements TrendSource, TrendDocument, TrendInsight, TrendTaxonomy, ParsingFailureQueue.
Includes proper indexes for query performance per SPEC-02 requirements.
"""
from django.db import models
from shared.infrastructure.orm.base_model import TimestampedModel


class TrendSource(TimestampedModel):
    """Trend source ORM model.

    Represents a source (website, API, feed) for trend documents.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # Source information
    name = models.CharField(max_length=255, db_index=True)
    url = models.URLField(max_length=2048)
    domain = models.CharField(max_length=100, db_index=True)

    # Crawling configuration
    crawl_schedule = models.CharField(max_length=100)  # Cron expression
    trust_level = models.CharField(max_length=20)  # low, medium, high
    license = models.CharField(max_length=100)

    # Status
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "trend_knowledge_source"
        verbose_name = "Trend Source"
        verbose_name_plural = "Trend Sources"
        indexes = [
            models.Index(fields=["domain", "active"]),
            models.Index(fields=["active"]),
        ]


class TrendDocument(TimestampedModel):
    """Trend document ORM model.

    Represents a collected document from a trend source.
    Separates published_at from collected_at per SPEC-02 REQ-02-TREND-003.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # References
    source_id = models.UUIDField(db_index=True)

    # Document information
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=2048)

    # Timestamps - separated per SPEC requirement
    published_at = models.DateTimeField(db_index=True)
    collected_at = models.DateTimeField(db_index=True)

    # Storage URIs
    raw_uri = models.CharField(max_length=2048)
    parsed_text_uri = models.CharField(max_length=2048, null=True, blank=True)

    # Deduplication and status
    hash = models.CharField(max_length=64, db_index=True)  # SHA-256
    parse_status = models.CharField(
        max_length=20,
        db_index=True,
        choices=[
            ("pending", "Pending"),
            ("parsing", "Parsing"),
            ("parsed", "Parsed"),
            ("failed", "Failed"),
        ],
    )

    class Meta:
        db_table = "trend_knowledge_document"
        verbose_name = "Trend Document"
        verbose_name_plural = "Trend Documents"
        indexes = [
            models.Index(fields=["source_id", "collected_at"]),
            models.Index(fields=["parse_status"]),
            models.Index(fields=["hash"]),
        ]


class TrendInsight(TimestampedModel):
    """Trend insight ORM model.

    Represents an extracted insight with evidence and confidence.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # References
    document_id = models.UUIDField(db_index=True)

    # Insight content
    summary = models.TextField()
    keywords = models.JSONField(default=list)  # List of keywords
    domain_tags = models.JSONField(default=list)  # List of domain tags
    evidence_quote = models.TextField()  # Direct quote for citation

    # Scores
    confidence = models.FloatField()  # 0.0 to 1.0
    recency_score = models.FloatField()  # 0.0 to 1.0

    class Meta:
        db_table = "trend_knowledge_insight"
        verbose_name = "Trend Insight"
        verbose_name_plural = "Trend Insights"
        indexes = [
            models.Index(fields=["document_id"]),
            models.Index(fields=["domain_tags"]),
        ]


class TrendTaxonomy(TimestampedModel):
    """Trend taxonomy ORM model.

    Data-driven taxonomy - NO hardcoded categories.
    Managed via admin console and seed data per SPEC-02 REQ-02-TREND-006.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # Taxonomy fields
    domain = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Hierarchical structure
    parent_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Status
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "trend_knowledge_taxonomy"
        verbose_name = "Trend Taxonomy"
        verbose_name_plural = "Trend Taxonomies"
        indexes = [
            models.Index(fields=["domain", "active"]),
            models.Index(fields=["category"]),
            models.Index(fields=["parent_id"]),
        ]


class ParsingFailureQueue(TimestampedModel):
    """Parsing failure queue ORM model.

    Tracks failed documents for admin review and retry.
    Exposed in admin console per SPEC-02 REQ-02-TREND-007.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # References
    document_id = models.UUIDField(db_index=True, unique=True)

    # Failure information
    reason = models.TextField()
    retried_count = models.IntegerField(default=0)

    class Meta:
        db_table = "trend_knowledge_parsing_failure_queue"
        verbose_name = "Parsing Failure"
        verbose_name_plural = "Parsing Failures"
        indexes = [
            models.Index(fields=["document_id"]),
            models.Index(fields=["-created_at"]),
        ]
