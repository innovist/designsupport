"""DRF serializers for Trend Knowledge entities.

REST Framework serializers for domain entities.
"""
from rest_framework import serializers


class TrendSourceSerializer(serializers.Serializer):
    """Serializer for TrendSource entities."""

    id = serializers.UUIDField()
    url = serializers.URLField()
    source_type = serializers.CharField()
    domain = serializers.CharField()
    name = serializers.CharField()
    config = serializers.JSONField(default=dict)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class TrendDocumentSerializer(serializers.Serializer):
    """Serializer for TrendDocument entities."""

    id = serializers.UUIDField()
    source_id = serializers.UUIDField()
    title = serializers.CharField()
    raw_storage_uri = serializers.URLField()
    content_hash = serializers.CharField()
    parsed_text = serializers.CharField(allow_blank=True, required=False)
    status = serializers.CharField()
    parsed_at = serializers.DateTimeField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()


class TrendInsightSerializer(serializers.Serializer):
    """Serializer for TrendInsight entities."""

    id = serializers.UUIDField()
    document_id = serializers.UUIDField()
    summary = serializers.CharField()
    keywords = serializers.ListField(child=serializers.CharField())
    evidence_quote = serializers.CharField(allow_blank=True, required=False)
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    created_at = serializers.DateTimeField()


class TrendTaxonomySerializer(serializers.Serializer):
    """Serializer for TrendTaxonomy entities."""

    id = serializers.UUIDField()
    domain = serializers.CharField()
    category = serializers.CharField()
    subcategories = serializers.ListField(child=serializers.CharField())
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class SearchTrendRequestSerializer(serializers.Serializer):
    """Serializer for trend search requests."""

    query = serializers.CharField(required=True, allow_blank=False)
    domain = serializers.CharField(required=False, allow_null=True)
    min_confidence = serializers.FloatField(
        required=False,
        default=0.0,
        min_value=0.0,
        max_value=1.0,
    )
    max_results = serializers.IntegerField(required=False, allow_null=True)


class TrendSearchResponseSerializer(serializers.Serializer):
    """Serializer for trend search responses."""

    insights = TrendInsightSerializer(many=True)
    total = serializers.IntegerField()
    has_more = serializers.BooleanField()
    insufficient_evidence = serializers.BooleanField()


class RegisterSourceRequestSerializer(serializers.Serializer):
    """Serializer for source registration requests."""

    url = serializers.URLField(required=True)
    source_type = serializers.ChoiceField(
        choices=["rss", "api", "scrape"],
        required=True,
    )
    domain = serializers.CharField(required=True)
    name = serializers.CharField(required=False, allow_null=True)
    config = serializers.JSONField(required=False, default=dict)
