"""
AbstractionRule model - the design grammar derived from references or sketches.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AbstractionRule(Base, TimestampMixin):
    """
    Design abstraction rules derived from a reference or sketch.

    INVARIANT: axes_count must be >= 2 before the rule can be used for image
    generation. Enforcement is in the use-case layer, not the DB.

    source_type: 'reference' | 'sketch'
    source_id: UUID of the originating ReferenceAsset or UserSketchAsset.
    """

    # @MX:NOTE: [AUTO] axes_count < 2 blocks GeneratedDesign creation; validate in use-case
    __tablename__ = "abstraction_rule"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    form: Mapped[str | None] = mapped_column(Text, nullable=True)
    structure: Mapped[str | None] = mapped_column(Text, nullable=True)
    surface: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_material: Mapped[str | None] = mapped_column(Text, nullable=True)
    meaning: Mapped[str | None] = mapped_column(Text, nullable=True)
    usability: Mapped[str | None] = mapped_column(Text, nullable=True)
    axes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sketch_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # sketch-specific fields
    keep_silhouette: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengthen_structure: Mapped[str | None] = mapped_column(Text, nullable=True)
    unclear_functions: Mapped[str | None] = mapped_column(Text, nullable=True)
    refinement_directions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    preserve_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    expand_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
