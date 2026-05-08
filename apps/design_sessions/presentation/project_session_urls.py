"""URL patterns for project-scoped session creation."""
from django.urls import path

from apps.design_sessions.presentation.views import SessionCreateAPIView

urlpatterns = [
    path("", SessionCreateAPIView.as_view(), name="project-session-create"),
]
