"""Workspace onboarding signals."""
from uuid import uuid4

from django.db import transaction

from apps.workspaces.infrastructure.orm.models import Membership, Tenant, Workspace


def ensure_default_workspace(sender, instance, created, **kwargs):
    """Create a real tenant/workspace membership for newly registered users."""
    if not created or instance.default_workspace_id:
        return

    tenant_name = f"{instance.display_name}'s Organization"
    workspace_name = f"{instance.display_name}'s Workspace"

    with transaction.atomic():
        tenant = Tenant.objects.create(
            id=str(uuid4()),
            name=tenant_name,
            plan="free",
            is_active=True,
        )
        workspace_id = uuid4()
        workspace = Workspace.all_objects.create(
            id=workspace_id,
            tenant_id=tenant.id,
            workspace_id=workspace_id,
            name=workspace_name,
            description="",
            is_active=True,
        )
        Membership.objects.create(
            user_id=instance.id,
            workspace_id=workspace.id,
            role="admin",
        )
        sender.objects.filter(id=instance.id, default_workspace_id__isnull=True).update(
            default_workspace_id=workspace.id
        )
