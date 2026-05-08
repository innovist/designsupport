"""Django app configuration for prompt_library module."""
from django.apps import AppConfig


class PromptLibraryConfig(AppConfig):
    """Configuration for prompt_library app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.prompt_library'
    verbose_name = 'Prompt Library'

    def ready(self):
        """Perform initialization when app is ready."""
        # Import signal handlers if needed
        pass
