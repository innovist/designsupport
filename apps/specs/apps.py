from django.apps import AppConfig


class specsConfig(AppConfig):
    """specs module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.specs'
    verbose_name = 'specs'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.specs.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
