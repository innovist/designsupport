"""Presentation layer for generation module.

This module contains DRF views, serializers, and URL configuration.
"""

from apps.generation.presentation.views import (
    GenerationJobViewSet,
    GenerationJobStatusView
)

from apps.generation.presentation.serializers import (
    CreateGenerationJobSerializer,
    GenerationJobSerializer,
    GeneratedDesignSerializer,
    ExecuteJobSerializer,
    ExecuteJobResponseSerializer
)

__all__ = [
    # Views
    "GenerationJobViewSet",
    "GenerationJobStatusView",

    # Serializers
    "CreateGenerationJobSerializer",
    "GenerationJobSerializer",
    "GeneratedDesignSerializer",
    "ExecuteJobSerializer",
    "ExecuteJobResponseSerializer",
]
