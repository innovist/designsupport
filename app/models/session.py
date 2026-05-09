"""
Session, Brief, and ChatMessage ORM models.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DesignSession(Base, TimestampMixin):
    """
    Represents one design work session within a project.

    pipeline_stage progression:
      brief_input -> trend -> concepting -> referencing
      -> abstracting -> generating -> documenting -> review_ready
      -> failed | completed
    """

    __tablename__ = "design_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_project.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="chatbot")
    pipeline_stage: Mapped[str] = mapped_column(
        String(50), nullable=False, default="brief_input"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    auto_progress_log: Mapped[list | None] = mapped_column(JSON, nullable=True)
    review_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["DesignProject"] = relationship(  # type: ignore[name-defined]
        "DesignProject", back_populates="sessions"
    )
    brief: Mapped["DesignBrief"] = relationship(
        "DesignBrief", back_populates="session", uselist=False
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", order_by="ChatMessage.created_at"
    )


class DesignBrief(Base, TimestampMixin):
    """
    Structured design brief extracted from user conversation.

    is_complete becomes True only when all mandatory fields are present
    and the user has confirmed the brief via chat.
    """

    __tablename__ = "design_brief"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_brief_session"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_user: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_case: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_form: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    session: Mapped["DesignSession"] = relationship("DesignSession", back_populates="brief")


class ChatMessage(Base):
    """
    Single message in a session conversation.
    evidence_links stores source URLs that back AI-generated content.
    """

    __tablename__ = "chat_message"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    evidence_links: Mapped[list | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    session: Mapped["DesignSession"] = relationship("DesignSession", back_populates="messages")
