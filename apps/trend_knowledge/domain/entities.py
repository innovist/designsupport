"""Trend Knowledge domain entities.

Pure Python domain entities with no Django/external dependencies.
All entities use datetime.now(timezone.utc) instead of datetime.utcnow().
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class TrendDocumentStatus(str, Enum):
    """Document parsing lifecycle status."""

    RAW = "pending"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"


class TrendSourceType(str, Enum):
    """Trend source type classification."""

    RSS = "rss"
    API = "api"
    SCRAPE = "scrape"
    WEB = "web"


def _utcnow() -> datetime:
    """Get current UTC timestamp.

    Using datetime.now(timezone.utc) instead of deprecated datetime.utcnow().
    """
    return datetime.now(timezone.utc)


@dataclass
class TrendSource:
    """Trend source aggregate root entity.

    Represents a source (website, API, feed) for trend documents.
    Managed by admin console with crawling schedule and trust level.

    Attributes:
        id: Unique identifier
        name: Human-readable source name
        url: Source URL or endpoint
        domain: Domain category (industrial, fashion, visual, advertising)
        crawl_schedule: Cron expression for crawling schedule
        trust_level: Source trust rating (low, medium, high)
        license: License type for content from this source
        active: Whether source is active for crawling
    """

    id: UUID
    name: str
    url: str
    domain: str
    crawl_schedule: str
    trust_level: str
    license: str
    active: bool
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        name: str,
        url: str,
        domain: str,
        crawl_schedule: str,
        trust_level: str,
        license: str,
        active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id or uuid4()
        self.name = name
        self.url = url
        self.domain = domain
        self.crawl_schedule = crawl_schedule
        self.trust_level = trust_level
        self.license = license
        self.active = active
        self.created_at = created_at or _utcnow()
        self.updated_at = updated_at or _utcnow()

    def deactivate(self) -> None:
        """Deactivate the source for crawling."""
        if not self.active:
            return
        self.active = False
        self.updated_at = _utcnow()

    def activate(self) -> None:
        """Activate the source for crawling."""
        if self.active:
            return
        self.active = True
        self.updated_at = _utcnow()

    def update_schedule(self, new_schedule: str) -> None:
        """Update crawling schedule."""
        if self.crawl_schedule == new_schedule:
            return
        self.crawl_schedule = new_schedule
        self.updated_at = _utcnow()


@dataclass
class TrendDocument:
    """Trend document entity.

    Represents a collected document from a trend source.
    Separates published_at (original publication) from collected_at (collection time).

    Attributes:
        id: Unique identifier
        source_id: Reference to TrendSource
        title: Document title
        url: Document URL
        published_at: Original publication date
        collected_at: Collection timestamp
        raw_uri: Storage URI for raw file
        parsed_text_uri: Storage URI for parsed text (optional)
        hash: Content hash for deduplication
        parse_status: Parsing status (pending, parsing, parsed, failed)
    """

    id: UUID
    source_id: UUID
    title: str
    url: str
    published_at: datetime
    collected_at: datetime
    raw_uri: str
    parsed_text_uri: Optional[str]
    hash: str
    parse_status: str

    def __init__(
        self,
        source_id: UUID,
        title: str,
        url: str,
        published_at: datetime,
        raw_uri: str,
        hash: str,
        parse_status: str = "pending",
        id: Optional[UUID] = None,
        collected_at: Optional[datetime] = None,
        parsed_text_uri: Optional[str] = None,
    ):
        self.id = id or uuid4()
        self.source_id = source_id
        self.title = title
        self.url = url
        self.published_at = published_at
        self.collected_at = collected_at or _utcnow()
        self.raw_uri = raw_uri
        self.parsed_text_uri = parsed_text_uri
        self.hash = hash
        self.parse_status = parse_status

    def mark_parsing(self) -> None:
        """Mark document as being parsed."""
        if self.parse_status != "pending":
            return
        self.parse_status = "parsing"

    def mark_parsed(self, parsed_text_uri: str) -> None:
        """Mark document as successfully parsed."""
        self.parse_status = "parsed"
        self.parsed_text_uri = parsed_text_uri

    def mark_failed(self) -> None:
        """Mark document as failed to parse."""
        self.parse_status = "failed"
        self.parsed_text_uri = None


@dataclass
class TrendInsight:
    """Trend insight entity.

    Represents an extracted insight from a trend document.
    Includes evidence quote for citation and confidence score.

    Attributes:
        id: Unique identifier
        document_id: Reference to TrendDocument
        summary: Insight summary text
        keywords: Extracted keywords
        domain_tags: Domain classification tags
        evidence_quote: Direct quote from document as evidence
        confidence: Confidence score (0.0 to 1.0)
        recency_score: Recency score (0.0 to 1.0, decreases with age)
    """

    id: UUID
    document_id: UUID
    summary: str
    keywords: list[str]
    domain_tags: list[str]
    evidence_quote: str
    confidence: float
    recency_score: float
    created_at: datetime

    def __init__(
        self,
        document_id: UUID,
        summary: str,
        keywords: list[str],
        domain_tags: list[str],
        evidence_quote: str,
        confidence: float,
        recency_score: float,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id or uuid4()
        self.document_id = document_id
        self.summary = summary
        self.keywords = keywords
        self.domain_tags = domain_tags
        self.evidence_quote = evidence_quote
        self.confidence = max(0.0, min(1.0, confidence))
        self.recency_score = max(0.0, min(1.0, recency_score))
        self.created_at = created_at or _utcnow()


@dataclass
class TrendTaxonomy:
    """Trend taxonomy entity.

    Data-driven taxonomy for categorizing trends.
    NO hardcoded categories - all managed via admin console and seed data.

    Attributes:
        id: Unique identifier
        domain: Domain category (industrial, fashion, visual, advertising)
        category: Category name (7 initial: Nature, Product, Architecture, etc.)
        label: Human-readable label
        description: Category description
        parent_id: Optional parent category ID for hierarchical structure
        active: Whether category is active
    """

    id: UUID
    domain: str
    category: str
    label: str
    description: str
    parent_id: Optional[UUID]
    active: bool
    created_at: datetime
    updated_at: datetime

    def __init__(
        self,
        domain: str,
        category: str,
        label: str,
        description: str,
        parent_id: Optional[UUID] = None,
        active: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id or uuid4()
        self.domain = domain
        self.category = category
        self.label = label
        self.description = description
        self.parent_id = parent_id
        self.active = active
        self.created_at = created_at or _utcnow()
        self.updated_at = updated_at or _utcnow()

    def deactivate(self) -> None:
        """Deactivate the taxonomy category."""
        if not self.active:
            return
        self.active = False
        self.updated_at = _utcnow()


@dataclass
class ParsingFailureQueue:
    """Parsing failure queue entity.

    Tracks documents that failed parsing for admin review and retry.
    Exposed in admin console for manual intervention.

    Attributes:
        id: Unique identifier
        document_id: Reference to failed TrendDocument
        reason: Failure reason
        created_at: Queue entry timestamp
        retried_count: Number of retry attempts
    """

    id: UUID
    document_id: UUID
    reason: str
    created_at: datetime
    retried_count: int

    def __init__(
        self,
        document_id: UUID,
        reason: str,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        retried_count: int = 0,
    ):
        self.id = id or uuid4()
        self.document_id = document_id
        self.reason = reason
        self.created_at = created_at or _utcnow()
        self.retried_count = retried_count

    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retried_count += 1
