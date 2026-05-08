"""URL configuration for References API.

DRF router and URL patterns.
"""
from django.urls import path

from apps.references.presentation.views import (
    ReferenceAnalysisView,
    ReferenceSearchView,
)

app_name = "references"

urlpatterns = [
    # Search endpoint
    path("search/", ReferenceSearchView.as_view({"post": "create"}), name="search"),

    # Analysis endpoint
    path(
        "analyze/<str:asset_id>/",
        ReferenceAnalysisView.as_view({"post": "create"}),
        name="analyze",
    ),
]
