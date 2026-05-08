"""Django admin configuration for trend knowledge models.

Admin interface for managing sources, documents, insights, taxonomy, and failures.
"""
from django.contrib import admin
from django.utils.html import format_html

from apps.trend_knowledge.infrastructure.orm.models import (
    ParsingFailureQueue,
    TrendDocument,
    TrendInsight,
    TrendSource,
    TrendTaxonomy,
)


@admin.register(TrendSource)
class TrendSourceAdmin(admin.ModelAdmin):
    """Admin interface for TrendSource."""

    list_display = [
        "name",
        "url",
        "domain",
        "crawl_schedule",
        "trust_level",
        "active",
        "created_at",
    ]
    list_filter = ["domain", "trust_level", "active"]
    search_fields = ["name", "url", "domain"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("Source Information", {
            "fields": ("name", "url", "domain"),
        }),
        ("Crawling Configuration", {
            "fields": ("crawl_schedule", "trust_level", "license"),
        }),
        ("Status", {
            "fields": ("active",),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(TrendDocument)
class TrendDocumentAdmin(admin.ModelAdmin):
    """Admin interface for TrendDocument."""

    list_display = [
        "title",
        "source_id",
        "url_link",
        "published_at",
        "collected_at",
        "parse_status",
        "created_at",
    ]
    list_filter = ["parse_status", "collected_at", "published_at"]
    search_fields = ["title", "url", "hash"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def url_link(self, obj):
        """Display URL as clickable link."""
        if obj.url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:50])
        return "-"
    url_link.short_description = "URL"

    fieldsets = (
        ("Document Information", {
            "fields": ("source_id", "title", "url"),
        }),
        ("Timestamps", {
            "fields": ("published_at", "collected_at"),
        }),
        ("Storage", {
            "fields": ("raw_uri", "parsed_text_uri"),
        }),
        ("Status", {
            "fields": ("hash", "parse_status"),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(TrendInsight)
class TrendInsightAdmin(admin.ModelAdmin):
    """Admin interface for TrendInsight."""

    list_display = [
        "summary_preview",
        "document_id",
        "domain_tags_list",
        "confidence",
        "recency_score",
        "created_at",
    ]
    list_filter = ["created_at", "confidence"]
    search_fields = ["summary", "keywords", "evidence_quote"]
    readonly_fields = ["id", "created_at"]

    def summary_preview(self, obj):
        """Display preview of summary."""
        if obj.summary:
            return obj.summary[:100] + "..." if len(obj.summary) > 100 else obj.summary
        return "-"
    summary_preview.short_description = "Summary"

    def domain_tags_list(self, obj):
        """Display domain tags as comma-separated list."""
        if obj.domain_tags:
            return ", ".join(obj.domain_tags)
        return "-"
    domain_tags_list.short_description = "Domain Tags"

    fieldsets = (
        ("Insight Content", {
            "fields": ("document_id", "summary", "keywords", "domain_tags"),
        }),
        ("Evidence & Scoring", {
            "fields": ("evidence_quote", "confidence", "recency_score"),
        }),
        ("Metadata", {
            "fields": ("id", "created_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(TrendTaxonomy)
class TrendTaxonomyAdmin(admin.ModelAdmin):
    """Admin interface for TrendTaxonomy.

    Data-driven taxonomy - NO hardcoded categories.
    Admin can activate/deactivate categories here.
    """

    list_display = [
        "label",
        "domain",
        "category",
        "parent_id",
        "active",
        "created_at",
    ]
    list_filter = ["domain", "category", "active"]
    search_fields = ["label", "description", "domain", "category"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("Taxonomy Information", {
            "fields": ("domain", "category", "label", "description"),
        }),
        ("Hierarchy", {
            "fields": ("parent_id",),
        }),
        ("Status", {
            "fields": ("active",),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(ParsingFailureQueue)
class ParsingFailureQueueAdmin(admin.ModelAdmin):
    """Admin interface for ParsingFailureQueue.

    Exposes failed documents for admin review and retry.
    """

    list_display = [
        "document_id",
        "reason_preview",
        "retried_count",
        "created_at",
    ]
    list_filter = ["retried_count", "created_at"]
    search_fields = ["document_id", "reason"]
    readonly_fields = ["id", "created_at"]

    def reason_preview(self, obj):
        """Display preview of failure reason."""
        if obj.reason:
            return obj.reason[:100] + "..." if len(obj.reason) > 100 else obj.reason
        return "-"
    reason_preview.short_description = "Reason"

    fieldsets = (
        ("Failure Information", {
            "fields": ("document_id", "reason"),
        }),
        ("Retry Status", {
            "fields": ("retried_count",),
        }),
        ("Metadata", {
            "fields": ("id", "created_at"),
            "classes": ("collapse",),
        }),
    )

    actions = ["retry_selected"]

    def retry_selected(self, request, queryset):
        """Retry selected failed documents.

        Args:
            request: HTTP request
            queryset: Selected failures

        Returns:
            Response message
        """
        from apps.trend_knowledge.infrastructure.tasks import parse_document_task

        count = 0
        for failure in queryset:
            if failure.retried_count < 3:
                parse_document_task.delay(str(failure.document_id))
                failure.retried_count += 1
                failure.save()
                count += 1

        self.message_user(request, f"Queued {count} documents for retry.")

    retry_selected.short_description = "Retry selected documents"
