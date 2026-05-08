"""Workspace API views."""
from uuid import uuid4

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.workspaces.infrastructure.orm.models import Membership, Tenant, Workspace


def _serialize_workspace(workspace: Workspace, role: str | None = None) -> dict:
    return {
        "id": str(workspace.id),
        "tenant_id": workspace.tenant_id,
        "name": workspace.name,
        "description": workspace.description,
        "is_active": workspace.is_active,
        "role": role,
    }


class WorkspaceListCreateAPIView(APIView):
    """List and create real workspaces for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        memberships = Membership.objects.filter(user_id=request.user.id)
        workspace_ids = [item.workspace_id for item in memberships]
        roles = {str(item.workspace_id): item.role for item in memberships}
        workspaces = Workspace.all_objects.filter(id__in=workspace_ids, is_active=True)
        return Response([
            _serialize_workspace(workspace, roles.get(str(workspace.id)))
            for workspace in workspaces
        ])

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)

        description = (request.data.get("description") or "").strip()
        tenant_id = self._resolve_tenant_id(request.user)
        workspace_id = uuid4()
        workspace = Workspace.all_objects.create(
            id=workspace_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            is_active=True,
        )
        Membership.objects.create(
            user_id=request.user.id,
            workspace_id=workspace.id,
            role="admin",
        )
        if not request.user.default_workspace_id:
            request.user.default_workspace_id = workspace.id
            request.user.save(update_fields=["default_workspace_id", "updated_at"])
        return Response(_serialize_workspace(workspace, "admin"), status=status.HTTP_201_CREATED)

    def _resolve_tenant_id(self, user) -> str:
        if user.default_workspace_id:
            workspace = Workspace.all_objects.get(id=user.default_workspace_id)
            return workspace.tenant_id

        tenant = Tenant.objects.create(
            id=str(uuid4()),
            name=f"{user.display_name}'s Organization",
            plan="free",
            is_active=True,
        )
        return tenant.id


class WorkspaceBootstrapAPIView(APIView):
    """Ensure older users have a default tenant/workspace."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.default_workspace_id:
            workspace = Workspace.all_objects.get(id=request.user.default_workspace_id)
            membership = Membership.objects.filter(
                user_id=request.user.id,
                workspace_id=workspace.id,
            ).first()
            return Response(_serialize_workspace(workspace, membership.role if membership else None))

        with transaction.atomic():
            tenant = Tenant.objects.create(
                id=str(uuid4()),
                name=f"{request.user.display_name}'s Organization",
                plan="free",
                is_active=True,
            )
            workspace_id = uuid4()
            workspace = Workspace.all_objects.create(
                id=workspace_id,
                tenant_id=tenant.id,
                workspace_id=workspace_id,
                name=f"{request.user.display_name}'s Workspace",
                description="",
                is_active=True,
            )
            Membership.objects.create(
                user_id=request.user.id,
                workspace_id=workspace.id,
                role="admin",
            )
            request.user.default_workspace_id = workspace.id
            request.user.save(update_fields=["default_workspace_id", "updated_at"])
        return Response(_serialize_workspace(workspace, "admin"), status=status.HTTP_201_CREATED)
