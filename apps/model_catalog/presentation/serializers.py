"""DRF serializers for model catalog API."""
from datetime import datetime
from typing import Any

from rest_framework import serializers

from apps.model_catalog.domain.entities import (
    AuthScheme,
    FeatureModelPolicy,
    ModelCatalog,
    ModelInvocation,
    ModelProvider,
    ModelType,
    PolicyChangeLog,
    PromptPolicy,
)


class ModelProviderSerializer(serializers.Serializer):
    """Serializer for ModelProvider entity."""

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255)
    api_key_env = serializers.CharField(max_length=255)
    base_url = serializers.URLField(max_length=500, required=False, allow_null=True)
    endpoint_path = serializers.CharField(max_length=255, required=False, allow_null=True)
    auth_scheme = serializers.ChoiceField(
        choices=[scheme.value for scheme in AuthScheme],
        default=AuthScheme.BEARER.value,
    )
    active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data: dict[str, Any]) -> ModelProvider:
        """Create a new provider."""
        import uuid

        return ModelProvider(
            id=f"prov-{uuid.uuid4().hex}",
            **validated_data,
        )

    def update(self, instance: ModelProvider, validated_data: dict[str, Any]) -> ModelProvider:
        """Update provider."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class ModelCatalogSerializer(serializers.Serializer):
    """Serializer for ModelCatalog entity."""

    id = serializers.CharField(read_only=True)
    provider_id = serializers.CharField(max_length=255)
    model_name = serializers.CharField(max_length=255)
    type = serializers.ChoiceField(
        choices=[mt.value for mt in ModelType],
    )
    context_limit = serializers.IntegerField(required=False, allow_null=True)
    cost_estimate = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        allow_null=True,
    )
    modalities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data: dict[str, Any]) -> ModelCatalog:
        """Create a new model catalog entry."""
        import uuid

        validated_data["type"] = ModelType(validated_data["type"])
        return ModelCatalog(
            id=f"mdl-{uuid.uuid4().hex}",
            **validated_data,
        )

    def update(self, instance: ModelCatalog, validated_data: dict[str, Any]) -> ModelCatalog:
        """Update model catalog entry."""
        if "type" in validated_data:
            validated_data["type"] = ModelType(validated_data["type"])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class FeatureModelPolicySerializer(serializers.Serializer):
    """Serializer for FeatureModelPolicy entity."""

    id = serializers.CharField(read_only=True)
    feature_key = serializers.CharField(max_length=255)
    primary_model_id = serializers.CharField(max_length=255)
    fallback_model_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    parameters = serializers.DictField(
        child=serializers.JSONField(),
        required=False,
    )
    max_cost_per_call = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        allow_null=True,
    )
    max_tokens = serializers.IntegerField(required=False, allow_null=True)
    version = serializers.IntegerField(read_only=True)
    active = serializers.BooleanField(default=True)
    reviewer = serializers.CharField(max_length=255, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data: dict[str, Any]) -> FeatureModelPolicy:
        """Create a new feature policy."""
        import uuid

        return FeatureModelPolicy(
            id=f"policy-{uuid.uuid4().hex}",
            version=1,
            **validated_data,
        )

    def update(self, instance: FeatureModelPolicy, validated_data: dict[str, Any]) -> FeatureModelPolicy:
        """Update feature policy."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class PromptPolicySerializer(serializers.Serializer):
    """Serializer for PromptPolicy entity."""

    id = serializers.CharField(read_only=True)
    feature_key = serializers.CharField(max_length=255)
    prompt_version = serializers.CharField(max_length=255)
    system_prompt = serializers.CharField()
    user_template = serializers.CharField()
    active = serializers.BooleanField(default=True)
    reviewer = serializers.CharField(max_length=255, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data: dict[str, Any]) -> PromptPolicy:
        """Create a new prompt policy."""
        import uuid

        return PromptPolicy(
            id=f"prompt-{uuid.uuid4().hex}",
            **validated_data,
        )

    def update(self, instance: PromptPolicy, validated_data: dict[str, Any]) -> PromptPolicy:
        """Update prompt policy."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class ModelInvocationSerializer(serializers.Serializer):
    """Serializer for ModelInvocation entity."""

    id = serializers.CharField(read_only=True)
    feature_key = serializers.CharField(max_length=255)
    tenant_id = serializers.CharField(max_length=255)
    workspace_id = serializers.CharField()
    session_id = serializers.CharField(required=False, allow_null=True)
    model_id = serializers.CharField(max_length=255)
    status = serializers.CharField()
    tokens_in = serializers.IntegerField(required=False, allow_null=True)
    tokens_out = serializers.IntegerField(required=False, allow_null=True)
    cost_estimate = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        allow_null=True,
    )
    latency_ms = serializers.IntegerField(required=False, allow_null=True)
    error_code = serializers.CharField(max_length=255, required=False, allow_null=True)
    error_summary = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class PolicyChangeLogSerializer(serializers.Serializer):
    """Serializer for PolicyChangeLog entity."""

    id = serializers.CharField(read_only=True)
    target_type = serializers.CharField(max_length=255)
    target_id = serializers.CharField(max_length=255)
    version_from = serializers.IntegerField(required=False, allow_null=True)
    version_to = serializers.IntegerField()
    actor_id = serializers.CharField(max_length=255)
    reason = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)


class InvokeModelRequestSerializer(serializers.Serializer):
    """Serializer for model invocation requests."""

    feature_key = serializers.CharField(max_length=255)
    payload = serializers.DictField()
    options = serializers.DictField(required=False)
    session_id = serializers.CharField(required=False, allow_null=True)


class InvokeModelResponseSerializer(serializers.Serializer):
    """Serializer for model invocation responses."""

    response = serializers.DictField()
    invocation_id = serializers.CharField()
    model_id = serializers.CharField()
    tokens_in = serializers.IntegerField(required=False, allow_null=True)
    tokens_out = serializers.IntegerField(required=False, allow_null=True)
    cost_estimate = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        required=False,
        allow_null=True,
    )
    latency_ms = serializers.IntegerField(required=False, allow_null=True)
