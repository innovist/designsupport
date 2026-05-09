"""
User sketch upload and AI sketch analysis models.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserSketchAsset(Base, TimestampMixin):
    """
    Original sketch file uploaded by the user.

    INVARIANT: file_path must never be overwritten - only soft-delete via is_deleted.
    Physical files are immutable once saved.
    """

    # @MX:NOTE: [AUTO] file_path is write-once; use is_deleted for removal
    __tablename__ = "user_sketch_asset"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(300), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    analysis: Mapped["SketchAnalysis"] = relationship(
        "SketchAnalysis", back_populates="sketch", uselist=False
    )

    @property
    def image_url(self) -> str:
        path = self.file_path.replace("\\", "/")
        marker = "uploads/"
        if marker in path:
            return "/" + path[path.index(marker):]
        if path.startswith("/"):
            return path
        return "/" + path.lstrip("/")

    @property
    def description(self) -> str | None:
        return self.user_memo or self.original_filename


class SketchAnalysis(Base, TimestampMixin):
    """
    AI interpretation of a user sketch.

    INVARIANT: intent_is_hypothesis is always True until the user explicitly
    confirms or corrects the interpretation via the confirm-analysis endpoint.
    """

    # @MX:NOTE: [AUTO] intent_is_hypothesis defaults to True; set False only after user_confirmed=True
    __tablename__ = "sketch_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sketch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sketch_asset.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent_is_hypothesis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    form_elements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    structure_elements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    unclear_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    questions_for_user: Mapped[list | None] = mapped_column(JSON, nullable=True)
    keep_elements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    vary_elements: Mapped[list | None] = mapped_column(JSON, nullable=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_corrections: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    sketch: Mapped["UserSketchAsset"] = relationship("UserSketchAsset", back_populates="analysis")
