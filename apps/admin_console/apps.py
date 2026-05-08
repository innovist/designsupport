from django.apps import AppConfig


class admin_consoleConfig(AppConfig):
    """admin console module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admin_console'
    verbose_name = 'admin console'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.admin_console.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
