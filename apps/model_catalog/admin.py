"""Django admin configuration for model catalog.

Implements REQ-04-ADMIN-001: Rich admin interfaces for model management.
"""
from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.model_catalog.infrastructure.orm.models import (
    ModelProviderModel,
    ModelCatalogModel,
    FeatureModelPolicyModel,
    PromptPolicyModel,
    ModelInvocationModel,
    PolicyChangeLogModel,
)


@admin.register(ModelProviderModel)
class ModelProviderAdmin(admin.ModelAdmin):
    """Admin interface for ModelProvider."""

    list_display = [
        "name",
        "api_key_env",
        "base_url_display",
        "auth_scheme",
        "active",
        "model_count",
        "created_at",
    ]
    list_filter = ["active", "auth_scheme", "created_at"]
    search_fields = ["name", "api_key_env", "base_url"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "name",
                    "api_key_env",
                    "active",
                )
            },
        ),
        (
            "API Configuration",
            {
                "fields": (
                    "base_url",
                    "endpoint_path",
                    "auth_scheme",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def base_url_display(self, obj):
        """Truncate base URL for display."""
        if obj.base_url:
            return obj.base_url[:50] + "..." if len(obj.base_url) > 50 else obj.base_url
        return "-"

    base_url_display.short_description = "Base URL"

    def get_queryset(self, request):
        """Optimize queryset with model count."""
        qs = super().get_queryset(request)
        return qs.annotate(model_count=Count("models"))

    def model_count(self, obj):
        """Display number of models for this provider."""
        return obj.model_count

    model_count.short_description = "Models"


@admin.register(ModelCatalogModel)
class ModelCatalogAdmin(admin.ModelAdmin):
    """Admin interface for ModelCatalog."""

    list_display = [
        "qualified_name",
        "provider",
        "type",
        "context_limit",
        "cost_estimate",
        "modalities_display",
        "active",
        "created_at",
    ]
    list_filter = ["type", "active", "provider", "created_at"]
    search_fields = ["model_name", "provider__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "provider",
                    "model_name",
                    "type",
                    "active",
                )
            },
        ),
        (
            "Model Specifications",
            {
                "fields": (
                    "context_limit",
                    "cost_estimate",
                    "modalities",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def qualified_name(self, obj):
        """Display fully qualified model name."""
        return f"{obj.provider.name}/{obj.model_name}"

    qualified_name.short_description = "Model"

    def modalities_display(self, obj):
        """Display modalities as badges."""
        if not obj.modalities:
            return "-"
        return ", ".join(obj.modalities)

    modalities_display.short_description = "Modalities"


@admin.register(FeatureModelPolicyModel)
class FeatureModelPolicyAdmin(admin.ModelAdmin):
    """Admin interface for FeatureModelPolicy."""

    list_display = [
        "feature_key",
        "primary_model_display",
        "fallback_count",
        "version",
        "active",
        "reviewer",
        "created_at",
    ]
    list_filter = ["feature_key", "active", "version", "created_at"]
    search_fields = ["feature_key", "primary_model__model_name", "reviewer"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "feature_key",
                    "version",
                    "active",
                    "reviewer",
                )
            },
        ),
        (
            "Model Configuration",
            {
                "fields": (
                    "primary_model",
                    "fallback_models",
                ),
            },
        ),
        (
            "Parameters & Limits",
            {
                "fields": (
                    "parameters",
                    "max_cost_per_call",
                    "max_tokens",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def primary_model_display(self, obj):
        """Display primary model with provider."""
        if obj.primary_model:
            return f"{obj.primary_model.provider.name}/{obj.primary_model.model_name}"
        return "-"

    primary_model_display.short_description = "Primary Model"

    def fallback_count(self, obj):
        """Display number of fallback models."""
        return obj.fallback_models.count()

    fallback_count.short_description = "Fallbacks"

    def get_queryset(self, request):
        """Optimize queryset with fallback count."""
        qs = super().get_queryset(request)
        return qs.select_related("primary_model__provider").prefetch_related("fallback_models")


@admin.register(PromptPolicyModel)
class PromptPolicyAdmin(admin.ModelAdmin):
    """Admin interface for PromptPolicy."""

    list_display = [
        "feature_key",
        "prompt_version",
        "active",
        "reviewer",
        "created_at",
    ]
    list_filter = ["feature_key", "active", "created_at"]
    search_fields = ["feature_key", "prompt_version", "system_prompt", "reviewer"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "feature_key",
                    "prompt_version",
                    "active",
                    "reviewer",
                )
            },
        ),
        (
            "Prompt Content",
            {
                "fields": (
                    "system_prompt",
                    "user_template",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ModelInvocationModel)
class ModelInvocationAdmin(admin.ModelAdmin):
    """Admin interface for ModelInvocation (read-only)."""

    list_display = [
        "id",
        "feature_key",
        "model_display",
        "tenant_id",
        "workspace_id",
        "status",
        "tokens_used",
        "cost_estimate",
        "latency_ms",
        "created_at",
    ]
    list_filter = ["status", "feature_key", "created_at"]
    search_fields = ["id", "feature_key", "tenant_id", "workspace_id", "session_id"]
    readonly_fields = [
        "id",
        "feature_key",
        "tenant_id",
        "workspace_id",
        "session_id",
        "model",
        "status",
        "tokens_in",
        "tokens_out",
        "cost_estimate",
        "latency_ms",
        "error_code",
        "error_summary",
        "created_at",
    ]

    def has_add_permission(self, request):
        """Disable add permission (read-only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable change permission (read-only)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Enable delete permission for cleanup."""
        return True

    def model_display(self, obj):
        """Display model with provider."""
        if obj.model:
            return f"{obj.model.provider.name}/{obj.model.model_name}"
        return "-"

    model_display.short_description = "Model"

    def tokens_used(self, obj):
        """Display total tokens."""
        if obj.tokens_in is not None and obj.tokens_out is not None:
            return obj.tokens_in + obj.tokens_out
        return "-"

    tokens_used.short_description = "Total Tokens"

    def get_queryset(self, request):
        """Optimize queryset with model relation."""
        qs = super().get_queryset(request)
        return qs.select_related("model__provider")


@admin.register(PolicyChangeLogModel)
class PolicyChangeLogAdmin(admin.ModelAdmin):
    """Admin interface for PolicyChangeLog (read-only)."""

    list_display = [
        "id",
        "target_type",
        "target_id",
        "version_change",
        "actor_id",
        "reason_preview",
        "created_at",
    ]
    list_filter = ["target_type", "created_at"]
    search_fields = ["target_id", "actor_id", "reason"]
    readonly_fields = [
        "id",
        "target_type",
        "target_id",
        "version_from",
        "version_to",
        "actor_id",
        "reason",
        "created_at",
    ]

    def has_add_permission(self, request):
        """Disable add permission (read-only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable change permission (read-only)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable delete permission (audit log)."""
        return False

    def version_change(self, obj):
        """Display version change."""
        if obj.version_from is not None:
            return f"{obj.version_from} → {obj.version_to}"
        return f"→ {obj.version_to}"

    version_change.short_description = "Version"

    def reason_preview(self, obj):
        """Display truncated reason."""
        if obj.reason:
            return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason
        return "-"

    reason_preview.short_description = "Reason"
