from django.apps import AppConfig


class model_catalogConfig(AppConfig):
    """model catalog module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.model_catalog'
    verbose_name = 'model catalog'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.model_catalog.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
