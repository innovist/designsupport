"""Tenant middleware for extracting and setting tenant context."""
from typing import Any
from uuid import UUID

from django.http import HttpRequest, HttpResponse


class TenantContext:
    """Thread-local storage for tenant context."""

    _tenant_id: str | None = None
    _workspace_id: UUID | None = None
    _user_id: UUID | None = None

    @classmethod
    def set(cls, tenant_id: str, workspace_id: UUID, user_id: UUID) -> None:
        """Set tenant context."""
        cls._tenant_id = tenant_id
        cls._workspace_id = workspace_id
        cls._user_id = user_id

    @classmethod
    def get(cls) -> tuple[str | None, UUID | None, UUID | None]:
        """Get tenant context."""
        return (cls._tenant_id, cls._workspace_id, cls._user_id)

    @classmethod
    def clear(cls) -> None:
        """Clear tenant context."""
        cls._tenant_id = None
        cls._workspace_id = None
        cls._user_id = None


class TenantMiddleware:
    """Middleware to extract tenant/workspace from request and set context."""

    def __init__(self, get_response: Any) -> None:
        """Initialize middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request to extract tenant context."""
        # Extract from session (set by authentication)
        tenant_id = request.session.get('tenant_id')
        workspace_id = request.session.get('workspace_id')
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None

        # Set context if authenticated
        if tenant_id and workspace_id and user_id:
            TenantContext.set(
                tenant_id=str(tenant_id),
                workspace_id=UUID(str(workspace_id)),
                user_id=UUID(str(user_id)),
            )

        # Process request
        response = self.get_response(request)

        # Clear context after request
        TenantContext.clear()

        return response
