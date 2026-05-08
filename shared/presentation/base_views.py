"""Base API views with tenant isolation and permission guards."""
from typing import Any

from django.http import HttpRequest
from rest_framework import permissions
from rest_framework.views import APIView

from shared.infrastructure.tenant_middleware.middleware import TenantContext


class TenantIsolationMixin:
    """Mixin to ensure tenant isolation in views."""

    def initial(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        """Extract tenant context before processing request."""
        super().initial(request, *args, **kwargs)
        tenant_id, workspace_id, user_id = TenantContext.get()

        if not (tenant_id and workspace_id and user_id):
            tenant_id, workspace_id, user_id = self._derive_context(request)
            if tenant_id and workspace_id and user_id:
                TenantContext.set(tenant_id, workspace_id, user_id)

        if not tenant_id or not workspace_id or not user_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Tenant context not available")

        # Store on request for use in views
        request.tenant_id = tenant_id  # type: ignore
        request.workspace_id = workspace_id  # type: ignore
        request.current_user_id = user_id  # type: ignore

    def _derive_context(self, request: HttpRequest):
        """Derive tenant context from the authenticated user's default workspace."""
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return (None, None, None)

        workspace_id = getattr(user, "default_workspace_id", None)
        if not workspace_id:
            return (None, None, getattr(user, "id", None))

        from apps.workspaces.infrastructure.orm.models import Workspace

        try:
            workspace = Workspace.all_objects.get(id=workspace_id, is_active=True)
        except Workspace.DoesNotExist:
            return (None, None, getattr(user, "id", None))

        return (workspace.tenant_id, workspace.id, getattr(user, "id", None))


class PermissionGuardMixin:
    """Mixin for role-based permission guards."""

    def check_permission(
        self,
        request: HttpRequest,
        required_roles: list[str],
    ) -> None:
        """Check if user has required role.

        Args:
            request: HTTP request
            required_roles: List of required roles

        Raises:
            PermissionDenied: If user lacks required role
        """
        if not request.user.is_authenticated:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed("Authentication required")

        user_role = getattr(request.user, 'role', None)

        if user_role not in required_roles:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                f"Role '{user_role}' not in required roles: {required_roles}"
            )


class BaseAPIView(TenantIsolationMixin, APIView):
    """Base API view with tenant isolation.

    All views should inherit from this to ensure tenant isolation.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Set in DRF settings

    def get_serializer_context(self) -> dict[str, Any]:
        """Add tenant context to serializer context."""
        context = super().get_serializer_context()
        context['tenant_id'] = getattr(self.request, 'tenant_id', None)
        context['workspace_id'] = getattr(self.request, 'workspace_id', None)
        context['user_id'] = getattr(self.request, 'current_user_id', None)
        return context


class AdminOnlyAPIView(PermissionGuardMixin, BaseAPIView):
    """Base view for admin-only endpoints."""

    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request: HttpRequest) -> None:
        """Check if user is admin."""
        super().check_permissions(request)
        self.check_permission(request, required_roles=['admin', 'tenant_admin'])
