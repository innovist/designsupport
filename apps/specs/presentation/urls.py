"""URL configuration for specs module."""
from django.urls import path

from apps.specs.presentation import views

app_name = "specs"

urlpatterns = [
    # Domain packs
    path("domain-packs/", views.list_domain_packs, name="list_domain_packs"),
    # Spec documents
    path("create/", views.create_spec, name="create_spec"),
    path("<uuid:spec_id>/", views.get_spec, name="get_spec"),
    path("<uuid:spec_id>/submit-for-review/", views.submit_for_review, name="submit_for_review"),
    path("<uuid:spec_id>/approve/", views.approve_spec, name="approve_spec"),
    path("<uuid:spec_id>/reject/", views.reject_spec, name="reject_spec"),
]
