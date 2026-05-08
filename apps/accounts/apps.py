"""Django AppConfig for accounts module."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Accounts module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Accounts & Authentication'

    def ready(self) -> None:
        """Import signals when app is ready."""
        import apps.accounts.infrastructure.signals  # noqa: F401
