"""DRF serializers for References entities.

REST Framework serializers for reference assets and analysis.
"""
from rest_framework import serializers


class ReferenceAssetSerializer(serializers.Serializer):
    """Serializer for ReferenceAsset entities."""

    id = serializers.CharField()
    provider = serializers.CharField()
    asset_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    thumbnail_url = serializers.URLField()
    original_url = serializers.URLField()
    license = serializers.JSONField()
    license_risk = serializers.CharField()  # "low", "medium", "high"
    attribution = serializers.JSONField(allow_null=True, required=False)
    metadata = serializers.JSONField()


class ReferenceAnalysisSerializer(serializers.Serializer):
    """Serializer for ReferenceAnalysis results."""

    asset_id = serializers.CharField()
    relevance_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    design_recommendations = serializers.ListField(child=serializers.CharField())
    color_palette = serializers.ListField(
        child=serializers.CharField(),
        allow_null=True,
        required=False,
    )
    style_tags = serializers.ListField(child=serializers.CharField())
    analyzed_at = serializers.DateTimeField()


class ReferenceClusterSerializer(serializers.Serializer):
    """Serializer for clustered reference results."""

    label = serializers.CharField()
    category = serializers.CharField()
    assets = ReferenceAssetSerializer(many=True)


class SearchReferenceRequestSerializer(serializers.Serializer):
    """Serializer for reference search requests."""

    query_kind = serializers.ChoiceField(
        choices=["keyword", "by_image"],
        required=True,
    )
    payload = serializers.JSONField(required=True)
    session_id = serializers.CharField(required=False, allow_null=True)
    domain = serializers.CharField(required=False, allow_null=True)
    max_results = serializers.IntegerField(required=False, allow_null=True)


class ReferenceSearchResponseSerializer(serializers.Serializer):
    """Serializer for reference search responses."""

    results = ReferenceAssetSerializer(many=True)
    clusters = ReferenceClusterSerializer(many=True)
    total = serializers.IntegerField()
    providers_used = serializers.ListField(child=serializers.CharField())
    quota_remaining = serializers.JSONField()
    insufficient_evidence = serializers.BooleanField()
