"""URL configuration for workspaces app."""
from django.urls import path

from apps.workspaces.presentation.views import (
    WorkspaceBootstrapAPIView,
    WorkspaceListCreateAPIView,
)

urlpatterns = [
    path("", WorkspaceListCreateAPIView.as_view(), name="workspace-list-create"),
    path("bootstrap/", WorkspaceBootstrapAPIView.as_view(), name="workspace-bootstrap"),
]
