"""Trend Knowledge application DTOs.

Data transfer objects for use case inputs/outputs.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class TrendSourceDTO:
    """DTO for TrendSource entity."""
    id: str
    url: str
    source_type: str
    domain: str
    name: str
    config: dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: str


@dataclass
class TrendDocumentDTO:
    """DTO for TrendDocument entity."""
    id: str
    source_id: str
    title: str
    raw_storage_uri: str
    content_hash: str
    parsed_text: str | None
    status: str
    parsed_at: str | None
    created_at: str


@dataclass
class TrendInsightDTO:
    """DTO for TrendInsight entity."""
    id: str
    document_id: str
    summary: str
    keywords: list[str]
    evidence_quote: str
    confidence: float
    created_at: str


@dataclass
class TrendTaxonomyDTO:
    """DTO for TrendTaxonomy entity."""
    id: str
    domain: str
    category: str
    subcategories: list[str]
    is_active: bool
    created_at: str


@dataclass
class SearchTrendRequest:
    """Request DTO for trend search."""
    query: str
    domain: str | None = None
    date_range: tuple[datetime, datetime] | None = None
    min_confidence: float = 0.0
    max_results: int | None = None


@dataclass
class TrendSearchResponse:
    """Response DTO for trend search."""
    insights: list[dict[str, Any]]
    total: int
    has_more: bool
    insufficient_evidence: bool
