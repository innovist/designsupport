"""
Trend source, document, and insight models.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TrendSource(Base, TimestampMixin):
    """
    Configuration for a trend data source (RSS feed, website, API endpoint).
    """

    __tablename__ = "trend_source"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crawl_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    license_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    documents: Mapped[list["TrendDocument"]] = relationship(
        "TrendDocument", back_populates="source"
    )


class TrendDocument(Base, TimestampMixin):
    """
    A single article or page collected from a TrendSource.
    content_hash prevents storing duplicate content.
    """

    __tablename__ = "trend_document"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trend_source.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    raw_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    source: Mapped["TrendSource"] = relationship("TrendSource", back_populates="documents")
    insights: Mapped[list["TrendInsight"]] = relationship(
        "TrendInsight", back_populates="document"
    )


class TrendInsight(Base, TimestampMixin):
    """
    Distilled insight extracted from a TrendDocument.

    INVARIANT: evidence_quote is required. When the source cannot be directly
    cited, is_hypothesis must be True.
    """

    # @MX:NOTE: [AUTO] is_hypothesis=True means insight must NOT be used as concept evidence
    __tablename__ = "trend_insight"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trend_document.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_session.id", ondelete="CASCADE"), nullable=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    domain_tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence_quote: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    is_hypothesis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    document: Mapped["TrendDocument"] = relationship("TrendDocument", back_populates="insights")
