"""URL configuration for admin console presentation layer.

Routes all admin screens with proper namespacing.
"""
from django.urls import path

from apps.admin_console.presentation.views import (
    AuditLogsView,
    DashboardView,
    JobQueueView,
    MetricsView,
    ModelsListView,
    PoliciesListView,
    PolicyEditView,
    PromptPoliciesListView,
    PromptPolicyEditView,
    ProviderCreateView,
    ProviderDeleteView,
    ProviderUpdateView,
    ProvidersListView,
    RollbackView,
)

app_name = "admin"

urlpatterns = [
    # Dashboard
    path("", DashboardView.as_view(), name="dashboard"),

    # Model Providers
    path("providers/", ProvidersListView.as_view(), name="providers"),
    path("providers/create/", ProviderCreateView.as_view(), name="provider_create"),
    path("providers/<str:provider_id>/update/", ProviderUpdateView.as_view(), name="provider_update"),
    path("providers/<str:provider_id>/delete/", ProviderDeleteView.as_view(), name="provider_delete"),

    # Models
    path("models/", ModelsListView.as_view(), name="models"),

    # Feature Policies
    path("policies/", PoliciesListView.as_view(), name="policies"),
    path("policies/<str:feature_key>/edit/", PolicyEditView.as_view(), name="policy_edit"),

    # Prompt Policies
    path("prompt-policies/", PromptPoliciesListView.as_view(), name="prompt_policies"),
    path("prompt-policies/<str:feature_key>/edit/", PromptPolicyEditView.as_view(), name="prompt_policy_edit"),

    # Metrics
    path("metrics/", MetricsView.as_view(), name="metrics"),

    # Audit Logs
    path("audit-logs/", AuditLogsView.as_view(), name="audit_logs"),

    # Rollback
    path("rollback/", RollbackView.as_view(), name="rollback"),

    # Job Queue
    path("job-queue/", JobQueueView.as_view(), name="job_queue"),
]
