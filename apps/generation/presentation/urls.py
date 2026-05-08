"""URL configuration for generation module."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.generation.presentation.views import GenerationJobViewSet, GenerationJobStatusView


# ViewSet router
router = DefaultRouter()
router.register(r"jobs", GenerationJobViewSet, basename="generation-job")

urlpatterns = [
    # ViewSet routes
    path("", include(router.urls)),

    # Custom routes
    path("jobs/status/", GenerationJobStatusView.as_view(), name="generation-job-status"),
]
