from django.apps import AppConfig


class design_sessionsConfig(AppConfig):
    """design sessions module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.design_sessions'
    verbose_name = 'design sessions'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.design_sessions.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
