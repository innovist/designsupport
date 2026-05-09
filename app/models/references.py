"""
Reference asset and analysis models.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ReferenceAsset(Base, TimestampMixin):
    """
    External or internal reference image/article collected for inspiration.

    high_risk_blocked=True prevents the reference from being used as a
    direct design input; users can still view but not apply it.
    """

    __tablename__ = "reference_asset"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=False
    )
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, default="external")
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_domain: Mapped[str | None] = mapped_column(String(200), nullable=True)
    license_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    copyright_risk: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    high_risk_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    domain_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    relevance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstraction_elements: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    analysis: Mapped["ReferenceAnalysis"] = relationship(
        "ReferenceAnalysis", back_populates="reference", uselist=False
    )

    @property
    def source_url(self) -> str | None:
        return self.url

    @property
    def thumbnail_url(self) -> str | None:
        return self.thumbnail_path or self.url


class ReferenceAnalysis(Base, TimestampMixin):
    """
    AI-generated formal analysis of a reference asset.
    replication_risk guards against near-copy outputs.
    """

    __tablename__ = "reference_analysis"
    __table_args__ = (
        UniqueConstraint("reference_id", name="uq_ref_analysis_reference"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reference_asset.id", ondelete="CASCADE"),
        nullable=False,
    )
    form_grammar: Mapped[str | None] = mapped_column(Text, nullable=True)
    structure_grammar: Mapped[str | None] = mapped_column(Text, nullable=True)
    material_direction: Mapped[str | None] = mapped_column(Text, nullable=True)
    meaning_symbols: Mapped[str | None] = mapped_column(Text, nullable=True)
    usability_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    replication_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    abstraction_fitness: Mapped[float | None] = mapped_column(Float, nullable=True)

    reference: Mapped["ReferenceAsset"] = relationship(
        "ReferenceAsset", back_populates="analysis"
    )
