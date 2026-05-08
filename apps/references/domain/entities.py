"""References domain entities.

Pure Python domain entities with no Django/external dependencies.
All entities use datetime.now(timezone.utc) instead of datetime.utcnow().
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


def _utcnow() -> datetime:
    """Get current UTC timestamp.

    Using datetime.now(timezone.utc) instead of deprecated datetime.utcnow().
    """
    return datetime.now(timezone.utc)


@dataclass
class ReferenceAsset:
    """Reference asset aggregate root entity.

    Represents a reference material (image, document, web page, internal asset).
    Used for visual inspiration and analysis in design concepts.

    Attributes:
        id: Unique identifier
        session_id: Design session ID
        kind: Asset type (image, document, internal, web_page)
        provider: Source provider (unsplash, pexels, pixabay, etc.)
        tier: Provider tier (1, 2, 3)
        thumbnail_uri: Storage URI for thumbnail (max 1024px, WebP)
        thumbnail_max_edge_px: Maximum edge of thumbnail (must be <= 1024)
        title: Asset title
        author: Author/creator name
        source_url: Original source URL
        external_url: External provider URL
        collected_at: Collection timestamp
        published_at: Original publication date
        license_id: SPDX or provider license identifier
        license_risk: License risk level (low, medium, high, unknown)
        attribution_text: Attribution text for display
        domain_tags: Domain classification tags
        relevance_reason: AI-explained relevance to search query
        abstractable_elements: Elements suitable for abstraction
        copy_risk: Risk level for direct copying
    """

    id: UUID
    session_id: UUID
    kind: str
    provider: str
    tier: int
    thumbnail_uri: str
    thumbnail_max_edge_px: int
    title: str
    author: Optional[str]
    source_url: Optional[str]
    external_url: Optional[str]
    collected_at: datetime
    published_at: Optional[datetime]
    license_id: str
    license_risk: str
    attribution_text: str
    domain_tags: list[str]
    relevance_reason: Optional[str]
    abstractable_elements: list[str]
    copy_risk: str
    created_at: datetime

    def __init__(
        self,
        session_id: UUID,
        kind: str,
        provider: str,
        tier: int,
        thumbnail_uri: str,
        title: str,
        license_id: str,
        license_risk: str,
        attribution_text: str,
        thumbnail_max_edge_px: int = 1024,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
        external_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        domain_tags: Optional[list[str]] = None,
        relevance_reason: Optional[str] = None,
        abstractable_elements: Optional[list[str]] = None,
        copy_risk: str = "unknown",
        id: Optional[UUID] = None,
        collected_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ):
        # Validate tier
        if tier not in {1, 2, 3}:
            raise ValueError(f"Tier must be 1, 2, or 3, got {tier}")

        # Validate thumbnail constraint
        if thumbnail_max_edge_px > 1024:
            raise ValueError(
                f"Thumbnail max edge must be <= 1024px, got {thumbnail_max_edge_px}"
            )

        # Validate kind
        valid_kinds = {"image", "document", "internal", "web_page"}
        if kind not in valid_kinds:
            raise ValueError(f"Kind must be one of {valid_kinds}, got {kind}")

        self.id = id or uuid4()
        self.session_id = session_id
        self.kind = kind
        self.provider = provider
        self.tier = tier
        self.thumbnail_uri = thumbnail_uri
        self.thumbnail_max_edge_px = thumbnail_max_edge_px
        self.title = title
        self.author = author
        self.source_url = source_url
        self.external_url = external_url
        self.collected_at = collected_at or _utcnow()
        self.published_at = published_at
        self.license_id = license_id
        self.license_risk = license_risk
        self.attribution_text = attribution_text
        self.domain_tags = domain_tags or []
        self.relevance_reason = relevance_reason
        self.abstractable_elements = abstractable_elements or []
        self.copy_risk = copy_risk
        self.created_at = created_at or _utcnow()

    def can_apply_direct_style(self) -> bool:
        """Check if direct style application is allowed.

        Returns False for tier 3 or high license risk (invariants).
        """
        if self.tier == 3:
            return False
        if self.license_risk == "high":
            return False
        return True


@dataclass
class ReferenceAnalysis:
    """Reference analysis entity.

    Structured analysis of a reference asset.
    Extracts form, structure, material, and symbol analysis.

    Attributes:
        id: Unique identifier
        asset_id: Reference to ReferenceAsset
        relevance: Relevance score (0.0 to 1.0)
        form_grammar: Form grammar analysis
        structure_grammar: Structure grammar analysis
        material_note: Material observations
        symbol_note: Symbol analysis
        copy_risk: Copy risk assessment
        created_at: Analysis timestamp
    """

    id: UUID
    asset_id: UUID
    relevance: float
    form_grammar: Optional[str]
    structure_grammar: Optional[str]
    material_note: Optional[str]
    symbol_note: Optional[str]
    copy_risk: str
    created_at: datetime

    def __init__(
        self,
        asset_id: UUID,
        relevance: float,
        copy_risk: str,
        form_grammar: Optional[str] = None,
        structure_grammar: Optional[str] = None,
        material_note: Optional[str] = None,
        symbol_note: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id or uuid4()
        self.asset_id = asset_id
        self.relevance = max(0.0, min(1.0, relevance))
        self.form_grammar = form_grammar
        self.structure_grammar = structure_grammar
        self.material_note = material_note
        self.symbol_note = symbol_note
        self.copy_risk = copy_risk
        self.created_at = created_at or _utcnow()


@dataclass
class ReferenceQuery:
    """Reference query entity.

    Represents a search query for references.
    Tracks query history for analytics and optimization.

    Attributes:
        id: Unique identifier
        session_id: Design session ID
        query_kind: Query type (keyword, image, sketch, document, internal, expanded)
        payload: Query payload (JSON string)
        requested_by: User ID who requested
        created_at: Query timestamp
    """

    id: UUID
    session_id: UUID
    query_kind: str
    payload: str
    requested_by: UUID
    created_at: datetime

    def __init__(
        self,
        session_id: UUID,
        query_kind: str,
        payload: str,
        requested_by: UUID,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        # Validate query_kind
        valid_kinds = {
            "keyword",
            "image",
            "sketch",
            "document",
            "internal",
            "expanded",
        }
        if query_kind not in valid_kinds:
            raise ValueError(f"Query kind must be one of {valid_kinds}, got {query_kind}")

        self.id = id or uuid4()
        self.session_id = session_id
        self.query_kind = query_kind
        self.payload = payload
        self.requested_by = requested_by
        self.created_at = created_at or _utcnow()


@dataclass
class ImageProviderQuota:
    """Image provider quota management entity.

    Tracks API usage and rate limits per provider.
    Enables round-robin when limits are exceeded.

    Attributes:
        provider: Provider name (unsplash, pexels, etc.)
        daily_limit: Daily call limit
        used_today: Calls used today
        reset_at: Reset timestamp for daily counter
        active: Whether provider is active
        last_error_at: Last error timestamp
    """

    provider: str
    daily_limit: int
    used_today: int
    reset_at: datetime
    active: bool
    last_error_at: Optional[datetime]

    def __init__(
        self,
        provider: str,
        daily_limit: int,
        used_today: int = 0,
        reset_at: Optional[datetime] = None,
        active: bool = True,
        last_error_at: Optional[datetime] = None,
    ):
        self.provider = provider
        self.daily_limit = daily_limit
        self.used_today = used_today
        self.reset_at = reset_at or _utcnow()
        self.active = active
        self.last_error_at = last_error_at

    def can_make_call(self) -> bool:
        """Check if provider can make a call."""
        if not self.active:
            return False
        return self.used_today < self.daily_limit

    def increment_usage(self) -> None:
        """Increment usage counter."""
        self.used_today += 1

    def reset_if_needed(self) -> None:
        """Reset counter if reset time has passed."""
        if _utcnow() >= self.reset_at:
            self.used_today = 0
