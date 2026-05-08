"""URL configuration for Trend Knowledge API.

DRF router and URL patterns.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.trend_knowledge.presentation.views import (
    ParsingFailureListView,
    TrendSearchView,
    TrendSourceViewSet,
)

router = DefaultRouter()
router.register(r"sources", TrendSourceViewSet, basename="trendsource")

app_name = "trend_knowledge"

urlpatterns = [
    # Search endpoint
    path("search/", TrendSearchView.as_view({"post": "create"}), name="search"),

    # Parsing failures admin endpoint
    path(
        "parsing-failures/",
        ParsingFailureListView.as_view({"get": "list"}),
        name="parsing-failures",
    ),

    # Router URLs
    *router.urls,
]
