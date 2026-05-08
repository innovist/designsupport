from django.apps import AppConfig


class user_assetsConfig(AppConfig):
    """user assets module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user_assets'
    verbose_name = 'user assets'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            import apps.user_assets.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file
