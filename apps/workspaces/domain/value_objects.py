"""Workspace value objects.

Immutable value objects for the workspaces domain.
"""
from dataclasses import dataclass
from enum import Enum


class TenantPlan(Enum):
    """Tenant subscription plan value object.

    Defines available subscription tiers with associated limits.
    """

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

    # Plan limits
    _LIMITS = {
        FREE: {"max_workspaces": 1, "max_members_per_workspace": 3, "max_projects": 5},
        PRO: {"max_workspaces": 10, "max_members_per_workspace": 20, "max_projects": 100},
        ENTERPRISE: {
            "max_workspaces": float("inf"),
            "max_members_per_workspace": float("inf"),
            "max_projects": float("inf"),
        },
    }

    def get_limit(self, limit_type: str) -> int:
        """Get plan limit for a specific type.

        Args:
            limit_type: Type of limit (max_workspaces, max_members_per_workspace, max_projects)

        Returns:
            Limit value (or inf for unlimited)

        Raises:
            KeyError: If limit_type is invalid
        """
        return self._LIMITS[self.value][limit_type]

    def can_create_workspace(self, current_count: int) -> bool:
        """Check if tenant can create more workspaces.

        Args:
            current_count: Current number of workspaces

        Returns:
            True if under limit
        """
        return current_count < self.get_limit("max_workspaces")

    def can_add_member(self, current_members: int) -> bool:
        """Check if workspace can add more members.

        Args:
            current_members: Current member count

        Returns:
            True if under limit
        """
        return current_members < self.get_limit("max_members_per_workspace")
