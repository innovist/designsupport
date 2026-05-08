"""Django admin registration for references app."""
from django.contrib import admin

from apps.references.infrastructure.orm.models import (
    ReferenceAssetModel,
    ReferenceAnalysisModel,
    ReferenceQueryModel,
    ImageProviderQuotaModel,
)


@admin.register(ReferenceAssetModel)
class ReferenceAssetAdmin(admin.ModelAdmin):
    """Admin interface for ReferenceAsset."""

    list_display = [
        "id",
        "session_id",
        "kind",
        "provider",
        "tier",
        "title",
        "author",
        "license_id",
        "license_risk",
        "created_at",
    ]
    list_filter = ["kind", "provider", "tier", "license_risk", "created_at"]
    search_fields = ["title", "author", "id", "session_id"]
    readonly_fields = ["created_at", "collected_at", "published_at"]

    fieldsets = (
        ("Basic Info", {
            "fields": ("session_id", "kind", "provider", "tier", "title")
        }),
        ("Image URLs", {
            "fields": ("thumbnail_uri", "source_url", "external_url")
        }),
        ("Authorship & License", {
            "fields": ("author", "license_id", "license_risk", "attribution_text")
        }),
        ("Metadata", {
            "fields": ("domain_tags", "published_at", "collected_at", "created_at")
        }),
        ("Analysis", {
            "fields": ("relevance_reason", "abstractable_elements", "copy_risk")
        }),
    )


@admin.register(ReferenceAnalysisModel)
class ReferenceAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for ReferenceAnalysis."""

    list_display = [
        "id",
        "asset_id",
        "relevance",
        "copy_risk",
        "created_at",
    ]
    list_filter = ["copy_risk", "created_at"]
    search_fields = ["id", "asset_id"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Basic Info", {
            "fields": ("asset_id", "relevance", "copy_risk")
        }),
        ("Analysis", {
            "fields": ("form_grammar", "structure_grammar", "material_note", "symbol_note")
        }),
        ("Metadata", {
            "fields": ("created_at",)
        }),
    )


@admin.register(ReferenceQueryModel)
class ReferenceQueryAdmin(admin.ModelAdmin):
    """Admin interface for ReferenceQuery."""

    list_display = [
        "id",
        "session_id",
        "query_kind",
        "requested_by",
        "created_at",
    ]
    list_filter = ["query_kind", "created_at"]
    search_fields = ["id", "session_id", "requested_by"]
    readonly_fields = ["created_at"]


@admin.register(ImageProviderQuotaModel)
class ImageProviderQuotaAdmin(admin.ModelAdmin):
    """Admin interface for ImageProviderQuota."""

    list_display = [
        "provider",
        "daily_limit",
        "used_today",
        "reset_at",
        "active",
        "last_error_at",
    ]
    list_filter = ["active", "reset_at"]
    search_fields = ["provider"]
    readonly_fields = ["last_error_at"]

    fieldsets = (
        ("Quota Info", {
            "fields": ("provider", "daily_limit", "used_today", "active")
        }),
        ("Reset", {
            "fields": ("reset_at",)
        }),
        ("Error Tracking", {
            "fields": ("last_error_at",)
        }),
    )
