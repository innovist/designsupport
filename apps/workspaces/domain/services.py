"""Workspace domain services.

Business logic for workspace membership and permission checking.
"""
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from apps.accounts.domain.value_objects import Role


@dataclass
class WorkspaceMembershipInfo:
    """Value object containing workspace membership information."""

    workspace_id: UUID
    tenant_id: str
    role: Role


class WorkspaceMembershipService:
    """Domain service for workspace membership operations."""

    @staticmethod
    def check_permission(user_role: Role, required_permission: str) -> bool:
        """Check if user role has a specific permission.

        Args:
            user_role: User's role in workspace
            required_permission: Permission to check

        Returns:
            True if role has the permission
        """
        return user_role.can(required_permission)

    @staticmethod
    def can_modify_workspace(user_role: Role) -> bool:
        """Check if user can modify workspace settings.

        Args:
            user_role: User's role in workspace

        Returns:
            True if user can modify workspace
        """
        return user_role in {Role.ADMIN, Role.LEAD}

    @staticmethod
    def can_manage_members(user_role: Role) -> bool:
        """Check if user can manage workspace members.

        Args:
            user_role: User's role in workspace

        Returns:
            True if user can manage members
        """
        return user_role == Role.ADMIN

    @staticmethod
    def can_delete_workspace(user_role: Role) -> bool:
        """Check if user can delete workspace.

        Args:
            user_role: User's role in workspace

        Returns:
            True if user can delete workspace
        """
        return user_role == Role.ADMIN

    @staticmethod
    def filter_accessible_workspaces(
        memberships: List[WorkspaceMembershipInfo], workspace_ids: List[UUID]
    ) -> List[UUID]:
        """Filter workspaces that user has access to.

        Args:
            memberships: List of user's workspace memberships
            workspace_ids: List of workspace IDs to filter

        Returns:
            List of accessible workspace IDs
        """
        accessible_workspace_ids = {m.workspace_id for m in memberships}
        return [wid for wid in workspace_ids if wid in accessible_workspace_ids]

    @staticmethod
    def get_highest_role(memberships: List[WorkspaceMembershipInfo]) -> Optional[Role]:
        """Get user's highest role across all workspaces.

        Args:
            memberships: List of user's workspace memberships

        Returns:
            Highest role or None if no memberships
        """
        if not memberships:
            return None

        # Find highest role by hierarchy
        highest = memberships[0].role
        for membership in memberships[1:]:
            if membership.role.is_higher_or_equal(highest):
                highest = membership.role

        return highest
