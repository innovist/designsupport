"""
Concept candidate and decision tracking models.
"""

import uuid

from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ConceptCandidate(Base, TimestampMixin):
    """
    AI-generated or user-proposed design concept candidate.

    evidence_ids links to TrendInsight / ReferenceAsset IDs.
    trend_evidence stores denormalised quotes for quick display.
    Only insights with is_hypothesis=False should appear in evidence_ids.
    """

    __tablename__ = "concept_candidate"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    trend_evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    generated_by: Mapped[str] = mapped_column(String(20), nullable=False, default="ai")

    decisions: Mapped[list["ConceptDecision"]] = relationship(
        "ConceptDecision", back_populates="candidate"
    )


class ConceptDecision(Base, TimestampMixin):
    """
    Records the user's or system's decision on a concept candidate.

    decision values: adopt | hold | discard | explore
    """

    __tablename__ = "concept_decision"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("concept_candidate.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    decider: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    alternatives_considered: Mapped[list | None] = mapped_column(JSON, nullable=True)

    candidate: Mapped["ConceptCandidate"] = relationship(
        "ConceptCandidate", back_populates="decisions"
    )
