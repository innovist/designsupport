"""Application ports for design_sessions module.

Defines interfaces for external dependencies including cross-module ports.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from apps.design_sessions.domain.entities import (
    DecisionLog,
    DesignBrief,
    DesignSession,
)


class SessionRepositoryPort(ABC):
    """Repository port for DesignSession aggregate."""

    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> Optional[DesignSession]:
        """Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            DesignSession entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_workspace(self, workspace_id: UUID) -> List[DesignSession]:
        """List all sessions in a workspace.

        Args:
            workspace_id: Workspace UUID

        Returns:
            List of DesignSession entities
        """
        pass

    @abstractmethod
    async def list_by_project(self, project_id: UUID) -> List[DesignSession]:
        """List all sessions for a project.

        Args:
            project_id: Project UUID

        Returns:
            List of DesignSession entities
        """
        pass

    @abstractmethod
    async def save(self, session: DesignSession) -> DesignSession:
        """Save session (create or update).

        Args:
            session: DesignSession entity to save

        Returns:
            Saved DesignSession entity
        """
        pass


class BriefRepositoryPort(ABC):
    """Repository port for DesignBrief aggregate."""

    @abstractmethod
    async def get_by_session(self, session_id: UUID) -> Optional[DesignBrief]:
        """Get brief by session ID.

        Args:
            session_id: Session UUID

        Returns:
            DesignBrief entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def save(self, brief: DesignBrief) -> DesignBrief:
        """Save brief (create or update).

        Args:
            brief: DesignBrief entity to save

        Returns:
            Saved DesignBrief entity
        """
        pass


class DecisionLogRepositoryPort(ABC):
    """Repository port for DecisionLog aggregate."""

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> List[DecisionLog]:
        """List all decisions for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of DecisionLog entities
        """
        pass

    @abstractmethod
    async def save(self, decision: DecisionLog) -> DecisionLog:
        """Save decision log entry.

        Args:
            decision: DecisionLog entity to save

        Returns:
            Saved DecisionLog entity
        """
        pass


# Cross-module ports for dependencies


class ConversationPort(ABC):
    """Port for creating conversations in conversations module."""

    @abstractmethod
    async def create_conversation(
        self,
        session_id: UUID,
        user_id: UUID,
        tenant_id: str,
        workspace_id: UUID,
    ) -> UUID:
        """Create a new conversation for a session.

        Args:
            session_id: Design session UUID
            user_id: User UUID
            tenant_id: Tenant string ID
            workspace_id: Workspace UUID

        Returns:
            Created conversation UUID
        """
        pass


class AssetPort(ABC):
    """Port for handling sketch uploads in user_assets module."""

    @abstractmethod
    async def create_sketch_asset(
        self,
        session_id: UUID,
        user_id: UUID,
        file_path: str,
        file_hash: str,
        mime_type: str,
    ) -> UUID:
        """Create a sketch asset for a session.

        Args:
            session_id: Design session UUID
            user_id: User UUID
            file_path: Path to uploaded file
            file_hash: SHA-256 hash of file
            mime_type: MIME type of file

        Returns:
            Created sketch asset UUID
        """
        pass


class DesignSessionPort(ABC):
    """Port for design session operations.

    This is a facade port that combines session, brief, and decision operations.
    """

    @abstractmethod
    async def get_session_by_id(self, session_id: UUID) -> Optional[DesignSession]:
        """Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            DesignSession entity if found, None otherwise
        """
        pass


class ProjectPort(ABC):
    """Port for project-related operations in design_projects module."""

    @abstractmethod
    async def get_project_by_id(self, project_id: UUID) -> Optional[dict]:
        """Get project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project data dictionary if found, None otherwise
        """
        pass
