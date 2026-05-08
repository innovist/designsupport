"""URL patterns for prompt library API."""
from django.urls import path

from apps.prompt_library.presentation.views import (
    list_patterns,
    search_patterns,
    validate_prompt,
    log_violation,
)

app_name = 'prompt_library'

urlpatterns = [
    # Pattern endpoints
    path('patterns/', list_patterns, name='list_patterns'),
    path('patterns/search/', search_patterns, name='search_patterns'),

    # Validation endpoints
    path('prompts/validate/', validate_prompt, name='validate_prompt'),

    # Violation endpoints
    path('violations/', log_violation, name='log_violation'),
]
