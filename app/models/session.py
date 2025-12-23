"""
Session model
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class Session(BaseModel):
    """Session model"""

    __tablename__ = "sessions"

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="Project ID"
    )

    name = Column(
        String(200),
        nullable=False,
        comment="Session name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Session description"
    )

    is_active = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Active flag (0: inactive, 1: active)"
    )

    project = relationship(
        "Project",
        back_populates="sessions"
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, name='{self.name}', project_id={self.project_id})>"
