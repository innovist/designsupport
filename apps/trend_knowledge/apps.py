from django.apps import AppConfig


class trend_knowledgeConfig(AppConfig):
    """trend knowledge module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.trend_knowledge'
    verbose_name = 'trend knowledge'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.trend_knowledge.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
