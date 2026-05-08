"""References application DTOs.

Data transfer objects for use case inputs/outputs.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ReferenceAssetDTO:
    """DTO for ReferenceAsset entity."""
    id: str
    provider: str
    asset_type: str  # "image" or "video"
    title: str
    description: str | None
    thumbnail_url: str
    original_url: str
    license: dict[str, Any]
    license_risk: str  # "low", "medium", "high"
    attribution: dict[str, Any] | None
    metadata: dict[str, Any]
    created_at: str


@dataclass
class ReferenceAnalysisDTO:
    """DTO for ReferenceAnalysis results."""
    asset_id: str
    relevance_score: float
    design_recommendations: list[str]
    color_palette: list[str] | None
    style_tags: list[str]
    analyzed_at: str


@dataclass
class ReferenceCluster:
    """DTO for clustered reference results."""
    label: str
    category: str
    assets: list[dict[str, Any]]


@dataclass
class SearchReferenceRequest:
    """Request DTO for reference search."""
    query_kind: str  # "keyword" or "by_image"
    payload: dict[str, Any]
    session_id: str | None = None
    domain: str | None = None
    max_results: int | None = None


# Alias for backward compatibility
ReferenceSearchRequest = SearchReferenceRequest


@dataclass
class ReferenceSearchResponse:
    """Response DTO for reference search."""
    results: list[dict[str, Any]]
    clusters: list[dict[str, Any]]  # List of ReferenceCluster as dicts
    total: int
    providers_used: list[str]
    quota_remaining: dict[str, int]
    insufficient_evidence: bool


@dataclass
class NormalizedReferenceCard:
    """Normalized response card from all image search adapters.

    All adapters must return this format for consistent handling in application layer.
    """
    provider: str
    tier: int  # 1, 2, or 3
    external_url: str  # Original page URL (for attribution)
    source_url: str  # Image direct URL
    thumbnail_url: str  # Provider thumbnail URL
    title: str | None
    author: str | None
    license_id: str  # SPDX or "unknown"
    attribution_text: str
    license_url: str | None
    domain_tags: list[str]
    published_at: datetime | None
    collected_at: datetime
    raw_meta: dict[str, Any]  # Provider-specific raw metadata
