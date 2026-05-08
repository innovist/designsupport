"""URL configuration for audit_logs admin endpoints."""
from django.urls import path

from apps.audit_logs.presentation.views import AuditLogListView

urlpatterns = [
    path("", AuditLogListView.as_view(), name="audit-log-list"),
]
