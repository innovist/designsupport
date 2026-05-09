"""
GeneratedDesign and DesignEvaluation models.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class GeneratedDesign(Base, TimestampMixin):
    """
    A single design image produced by an AI image model.

    INVARIANT: rule_id is mandatory - no image may be generated without an
    AbstractionRule as evidence. Enforced in create_generation_job use-case.

    status: pending | processing | completed | failed
    """

    # @MX:ANCHOR: [AUTO] rule_id FK enforces evidence-based generation invariant
    # @MX:REASON: Designs without AbstractionRule violate the core pipeline contract

    __tablename__ = "generated_design"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("abstraction_rule.id", ondelete="RESTRICT"),
        nullable=False,
    )
    brief_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_brief.id", ondelete="SET NULL"), nullable=True
    )
    concept_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concept_candidate.id", ondelete="SET NULL"),
        nullable=True,
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_from_user_sketch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @property
    def image_url(self) -> str | None:
        if not self.image_path:
            return None
        if self.image_path.startswith(("http://", "https://", "/")):
            return self.image_path
        return f"/uploads/{self.image_path.lstrip('/')}"


class DesignEvaluation(Base, TimestampMixin):
    """
    Comparative evaluation of generated design candidates.
    discarded_with_reason records which alternatives were rejected and why.
    """

    __tablename__ = "design_evaluation"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    candidate_design_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    criteria: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    winner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    discarded_with_reason: Mapped[list | None] = mapped_column(JSON, nullable=True)
