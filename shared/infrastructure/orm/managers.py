"""Tenant-aware ORM manager and queryset for automatic tenant isolation.

REQ-01-TENANT-001: All workspace-scoped data auto-filtered by tenant_id and workspace_id.
INV-01-05: Cross-tenant data leakage prevented at ORM layer.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from django.db import models

# Thread-local bypass flag — context manager sets/clears it
_bypass_state: dict[str, bool] = {}


def _is_bypassed() -> bool:
    """Check if tenant filtering is bypassed for current execution context."""
    import threading
    return _bypass_state.get(str(threading.current_thread().ident), False)


def _set_bypass(value: bool) -> None:
    """Set bypass state for current thread."""
    import threading
    key = str(threading.current_thread().ident)
    if value:
        _bypass_state[key] = True
    else:
        _bypass_state.pop(key, None)


class TenantAwareQuerySet(models.QuerySet):
    """QuerySet that auto-filters by tenant_id and workspace_id from TenantContext.

    When TenantContext has an active tenant/workspace and bypass is not set,
    all queries are scoped to that tenant and workspace.
    """

    def _filter_tenant(self) -> "TenantAwareQuerySet":
        """Apply tenant/workspace filter from active TenantContext.

        Returns:
            Filtered QuerySet scoped to active tenant/workspace,
            or unfiltered if bypass is active or no context available.
        """
        if _is_bypassed():
            return self

        from shared.infrastructure.tenant_middleware.middleware import TenantContext

        tenant_id, workspace_id, _user_id = TenantContext.get()

        if tenant_id and workspace_id:
            return self.filter(tenant_id=tenant_id, workspace_id=workspace_id)

        return self


class TenantAwareManager(models.Manager):
    """Manager that returns TenantAwareQuerySet with auto tenant filtering.

    Models using this manager will automatically scope queries to the active
    tenant and workspace unless TenantContext.bypass() is active.

    Usage:
        class MyModel(TenantScopedModel):
            objects = TenantAwareManager()
            all_objects = models.Manager()  # Unfiltered escape hatch
    """

    def get_queryset(self) -> TenantAwareQuerySet:
        """Return tenant-filtered queryset.

        Returns:
            TenantAwareQuerySet filtered by active tenant context.
        """
        return TenantAwareQuerySet(self.model, using=self._db)._filter_tenant()


class TenantContext:
    """Extended TenantContext with bypass context manager.

    This class shadows shared.infrastructure.tenant_middleware.middleware.TenantContext
    to add bypass() support needed by admin/audit paths (REQ-01-AUDIT-001).

    IMPORTANT: Import this from shared.infrastructure.orm.managers when bypass()
    is needed. The middleware module's TenantContext handles the per-request
    set/get/clear lifecycle.
    """

    @staticmethod
    @contextmanager
    def bypass() -> Generator[None, None, None]:
        """Context manager that disables tenant auto-filtering.

        Use ONLY for admin/audit operations that legitimately need cross-tenant
        data access (e.g., AuditLog admin queries, migration scripts).

        Example:
            with TenantContext.bypass():
                all_logs = AuditLog.all_objects.all()
        """
        _set_bypass(True)
        try:
            yield
        finally:
            _set_bypass(False)
