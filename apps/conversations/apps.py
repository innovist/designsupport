from django.apps import AppConfig


class conversationsConfig(AppConfig):
    """conversations module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.conversations'
    verbose_name = 'conversations'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.conversations.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
