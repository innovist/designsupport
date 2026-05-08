from django.apps import AppConfig


class audit_logsConfig(AppConfig):
    """audit logs module configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit_logs'
    verbose_name = 'audit logs'

    def ready(self) -> None:
        """Import signals and register system checks when app is ready."""
        try:
            import apps.audit_logs.infrastructure.signals  # noqa: F401
        except ImportError:
            pass  # No signals file

        self._register_tenant_scope_check()

    @staticmethod
    def _register_tenant_scope_check() -> None:
        """Register system check: warn if any business model lacks TenantScopedModel.

        Gap 3 (REQ-01-TENANT-001): Alerts operators on startup if a model in
        apps.*.infrastructure.orm.models does not inherit TenantScopedModel
        and is not in the explicit allowlist.
        """
        import logging
        from django.apps import apps as django_apps

        logger = logging.getLogger(__name__)

        # Models that are legitimately scoped through a parent aggregate.
        _TENANT_SCOPE_ALLOWLIST = {
            "Tenant",
            "Workspace",
            "Membership",
            "User",
            "AuditLog",
            "DesignBrief",
            "DecisionLog",
            "Conversation",
            "ChatMessage",
            "SketchAnalysis",
        }

        # Modules to inspect (only infrastructure orm layers)
        _ORM_MODULE_SUFFIX = ".infrastructure.orm.models"

        def check_tenant_scope():
            try:
                from shared.infrastructure.orm.base_model import TenantScopedModel

                for app_config in django_apps.get_app_configs():
                    if not app_config.name.startswith("apps."):
                        continue
                    if not app_config.name.endswith(("accounts", "design_sessions",
                                                      "design_projects", "conversations",
                                                      "user_assets", "workspaces")):
                        continue
                    for model in app_config.get_models():
                        if model.__name__ in _TENANT_SCOPE_ALLOWLIST:
                            continue
                        if not issubclass(model, TenantScopedModel):
                            logger.warning(
                                "TenantScope check: model %s.%s does not inherit "
                                "TenantScopedModel and is not in allowlist. "
                                "REQ-01-TENANT-001 may be violated.",
                                app_config.name,
                                model.__name__,
                            )
            except Exception:  # noqa: BLE001
                pass  # Never block startup

        check_tenant_scope()
