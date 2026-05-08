from django.apps import AppConfig


class UworkspacesConfig(AppConfig):
    """workspaces module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workspaces'
    verbose_name = 'workspaces'

    def ready(self) -> None:
        """Import signals when app is ready."""
        try:
            from django.apps import apps
            from django.db.models.signals import post_save

            from apps.workspaces.infrastructure.signals import ensure_default_workspace

            post_save.connect(
                ensure_default_workspace,
                sender=apps.get_model("accounts", "User"),
                dispatch_uid="workspaces.ensure_default_workspace",
            )
        except ImportError:
            pass  # No signals file
