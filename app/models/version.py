"""
Version model
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class Version(BaseModel):
    """Version model"""

    __tablename__ = "versions"

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="Project ID"
    )

    version_number = Column(
        String(50),
        nullable=False,
        comment="Version number"
    )

    name = Column(
        String(200),
        nullable=True,
        comment="Version name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Version description"
    )

    is_current = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Current flag (0: no, 1: yes)"
    )

    changes = Column(
        Text,
        nullable=True,
        comment="Changes summary"
    )

    project = relationship(
        "Project",
        back_populates="versions"
    )

    def __repr__(self) -> str:
        return f"<Version(id={self.id}, version='{self.version_number}', project_id={self.project_id})>"
