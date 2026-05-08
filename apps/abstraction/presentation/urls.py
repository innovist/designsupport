"""URL routing for abstraction module."""
from django.urls import path

from apps.abstraction.presentation import views

app_name = "abstraction"

urlpatterns = [
    path(
        "rules/generate/",
        views.generate_abstraction_rules,
        name="generate-abstraction-rules",
    ),
    path(
        "prompts/generate/",
        views.generate_sketch_prompts,
        name="generate-sketch-prompts",
    ),
    path(
        "prompts/validate/",
        views.validate_prompt_safety,
        name="validate-prompt-safety",
    ),
]
