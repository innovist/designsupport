"""Design project domain entities.

Project organization and domain classification.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
from uuid import UUID, uuid4
from typing import Optional
from enum import Enum


class ProjectStatus(Enum):
    """Project status value object."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DomainType(Enum):
    """Design domain classification."""

    INDUSTRIAL = "industrial"
    FASHION = "fashion"
    VISUAL = "visual"
    ADVERTISING = "advertising"

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        return {
            DomainType.INDUSTRIAL: "Industrial Design",
            DomainType.FASHION: "Fashion Design",
            DomainType.VISUAL: "Visual Design",
            DomainType.ADVERTISING: "Advertising Design",
        }[self]


@dataclass
class DesignProject:
    """Design project aggregate root.

    Organizes design sessions within a workspace.
    """

    id: UUID
    workspace_id: UUID
    title: str
    domain: DomainType
    status: ProjectStatus
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        workspace_id: UUID,
        title: str,
        domain: DomainType,
        owner_id: UUID,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize a new design project.

        Args:
            workspace_id: Workspace UUID
            title: Project title
            domain: Design domain
            owner_id: Owner user UUID
            status: Project status
            id: Project UUID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id or uuid4()
        self.workspace_id = workspace_id
        self.title = title
        self.domain = domain
        self.status = status
        self.owner_id = owner_id
        self.created_at = created_at or _utcnow()
        self.updated_at = updated_at or _utcnow()

    def archive(self) -> None:
        """Archive the project."""
        if self.status != ProjectStatus.ACTIVE:
            return
        self.status = ProjectStatus.ARCHIVED
        self.updated_at = _utcnow()

    def delete_soft(self) -> None:
        """Soft delete the project."""
        if self.status == ProjectStatus.DELETED:
            return
        self.status = ProjectStatus.DELETED
        self.updated_at = _utcnow()
