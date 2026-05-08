"""Account value objects.

Immutable value objects for the accounts domain.
"""
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet
from uuid import UUID


class Role(Enum):
    """User role within a workspace.

    Roles follow hierarchy: admin > lead > designer > viewer.
    Higher roles include all permissions of lower roles.
    """

    ADMIN = "admin"
    LEAD = "lead"
    DESIGNER = "designer"
    VIEWER = "viewer"

    def get_permissions(self) -> FrozenSet[str]:
        """Get all permissions for this role."""
        _PERMISSIONS: dict[str, frozenset[str]] = {
            "admin": frozenset({
                "manage_workspace", "manage_members", "manage_projects",
                "manage_settings", "delete_workspace", "view_all_projects",
                "create_project", "edit_project", "delete_project",
                "run_session", "view_session", "edit_session", "delete_session",
            }),
            "lead": frozenset({
                "manage_projects", "manage_settings", "view_all_projects",
                "create_project", "edit_project", "delete_project",
                "run_session", "view_session", "edit_session",
            }),
            "designer": frozenset({
                "create_project", "edit_project",
                "run_session", "view_session", "edit_session",
            }),
            "viewer": frozenset({"view_session"}),
        }
        return _PERMISSIONS[self.value]

    def can(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.get_permissions()

    def is_higher_or_equal(self, other: "Role") -> bool:
        """Check if this role is higher or equal in hierarchy."""
        hierarchy = {Role.VIEWER: 0, Role.DESIGNER: 1, Role.LEAD: 2, Role.ADMIN: 3}
        return hierarchy[self] >= hierarchy[other]


@dataclass(frozen=True)
class WorkspaceRole:
    """Workspace role value object.

    Combines workspace ID with user role for that workspace.
    """

    workspace_id: UUID
    role: Role

    def has_permission(self, permission: str) -> bool:
        """Check if this workspace role has a permission."""
        return self.role.can(permission)
