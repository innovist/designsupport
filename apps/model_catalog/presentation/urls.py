"""URL configuration for model catalog API."""
from django.urls import path

from apps.model_catalog.presentation import views

app_name = "model_catalog"

urlpatterns = [
    # Providers
    path("providers/", views.list_providers, name="list_providers"),
    path("providers/register/", views.register_provider, name="register_provider"),

    # Models
    path("models/", views.list_models, name="list_models"),
    path("models/register/", views.register_model, name="register_model"),

    # Invocations
    path("invocations/", views.InvokeModelView.as_view(), name="invoke_model"),

    # Feature Policies
    path("policies/features/", views.FeaturePolicyView.as_view(), name="feature_policies"),
    path(
        "policies/features/<str:id>/",
        views.FeaturePolicyView.as_view(),
        name="feature_policy_detail",
    ),
    path(
        "policies/features/<str:id>/rollback/",
        views.FeaturePolicyView.as_view(),
        {"action": "rollback"},
        name="feature_policy_rollback",
    ),

    # Metrics
    path("metrics/", views.get_model_metrics, name="get_metrics"),
]
