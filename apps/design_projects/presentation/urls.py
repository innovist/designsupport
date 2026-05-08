"""URL configuration for design_projects app."""
from django.urls import path

from apps.design_projects.presentation.views import ProjectDetailAPIView, ProjectListCreateAPIView

urlpatterns = [
    path("", ProjectListCreateAPIView.as_view(), name="project-list-create"),
    path("<uuid:pk>/", ProjectDetailAPIView.as_view(), name="project-detail"),
]
