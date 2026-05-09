"""
SpecDocument model - versioned design specification output.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SpecDocument(Base, TimestampMixin):
    """
    A versioned design specification document bundling all pipeline outputs.

    content_json structure (all keys required in generate_spec use-case):
      brief, trend_evidence, concept_candidates, final_concept,
      sketch_analysis, reference_board, abstraction_rules,
      generated_designs, discarded_alternatives, decision_rationale,
      sources, ai_usage_disclosure

    parent_version_id points to the previous SpecDocument for version history.
    """

    # @MX:NOTE: [AUTO] discarded_alternatives and decision_rationale are mandatory in content_json
    __tablename__ = "spec_document"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spec_document.id", ondelete="SET NULL"),
        nullable=True,
    )
