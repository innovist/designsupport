from django.apps import AppConfig


class {CLASS_NAME}Config(AppConfig):
    """{verbose_name} module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{module_name}'
    verbose_name = '{verbose_name}'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.{module_name}.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
