"""Django app configuration for abstraction module."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AbstractionConfig(AppConfig):
    """Configuration for the abstraction app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.abstraction"
    verbose_name = _("Abstraction")

    def ready(self):
        """Perform initialization when app is ready."""
        # Import signal handlers
        import apps.abstraction.infrastructure.signals  # noqa: F401
