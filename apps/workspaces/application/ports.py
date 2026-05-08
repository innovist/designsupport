"""Application ports for workspaces module.

Defines interfaces for external dependencies following Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from apps.workspaces.domain.entities import Membership, Tenant, Workspace


class TenantRepositoryPort(ABC):
    """Repository port for Tenant aggregate."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID.

        Args:
            tenant_id: Tenant string ID

        Returns:
            Tenant entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def save(self, tenant: Tenant) -> Tenant:
        """Save tenant (create or update).

        Args:
            tenant: Tenant entity to save

        Returns:
            Saved tenant entity
        """
        pass


class WorkspaceRepositoryPort(ABC):
    """Repository port for Workspace aggregate."""

    @abstractmethod
    async def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        """Get workspace by ID.

        Args:
            workspace_id: Workspace UUID

        Returns:
            Workspace entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[Workspace]:
        """List all workspaces where user is a member.

        Args:
            user_id: User UUID

        Returns:
            List of workspace entities
        """
        pass

    @abstractmethod
    async def save(self, workspace: Workspace) -> Workspace:
        """Save workspace (create or update).

        Args:
            workspace: Workspace entity to save

        Returns:
            Saved workspace entity
        """
        pass

    @abstractmethod
    async def exists_by_name(self, tenant_id: str, name: str) -> bool:
        """Check if workspace exists by name within tenant.

        Args:
            tenant_id: Tenant string ID
            name: Workspace name

        Returns:
            True if workspace exists, False otherwise
        """
        pass


class MembershipRepositoryPort(ABC):
    """Repository port for Membership aggregate."""

    @abstractmethod
    async def get_by_workspace_and_user(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> Optional[Membership]:
        """Get membership by workspace and user.

        Args:
            workspace_id: Workspace UUID
            user_id: User UUID

        Returns:
            Membership entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_workspace(self, workspace_id: UUID) -> List[Membership]:
        """List all memberships for a workspace.

        Args:
            workspace_id: Workspace UUID

        Returns:
            List of membership entities
        """
        pass

    @abstractmethod
    async def save(self, membership: Membership) -> Membership:
        """Save membership (create or update).

        Args:
            membership: Membership entity to save

        Returns:
            Saved membership entity
        """
        pass

    @abstractmethod
    async def delete(self, membership: Membership) -> None:
        """Delete membership.

        Args:
            membership: Membership entity to delete
        """
        pass
