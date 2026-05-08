from django.apps import AppConfig


class generationConfig(AppConfig):
    """generation module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.generation'
    verbose_name = 'generation'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.generation.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
