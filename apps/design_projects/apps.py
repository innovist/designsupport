from django.apps import AppConfig


class design_projectsConfig(AppConfig):
    """design projects module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.design_projects'
    verbose_name = 'design projects'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.design_projects.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
