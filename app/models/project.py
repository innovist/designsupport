"""
DesignProject model - top-level container grouping related design sessions.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DesignProject(Base, TimestampMixin):
    __tablename__ = "design_project"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    workspace: Mapped["Workspace"] = relationship(  # type: ignore[name-defined]
        "Workspace", back_populates="projects"
    )
    sessions: Mapped[list["DesignSession"]] = relationship(  # type: ignore[name-defined]
        "DesignSession", back_populates="project"
    )
