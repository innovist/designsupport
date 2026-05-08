from django.apps import AppConfig


class referencesConfig(AppConfig):
    """references module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.references'
    verbose_name = 'references'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.references.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
