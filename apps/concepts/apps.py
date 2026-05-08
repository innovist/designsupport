from django.apps import AppConfig


class conceptsConfig(AppConfig):
    """concepts module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.concepts'
    verbose_name = 'concepts'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.concepts.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
