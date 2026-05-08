"""Trend Knowledge domain events.

Events that represent important state changes in the trend knowledge domain.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID


def _utcnow() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass
class SourceRegistered:
    """Event fired when a new trend source is registered.

    Attributes:
        source_id: ID of the registered source
        name: Source name
        domain: Domain category
        occurred_at: Event timestamp
    """

    source_id: UUID
    name: str
    domain: str
    occurred_at: datetime

    def __init__(
        self,
        source_id: UUID,
        name: str,
        domain: str,
        occurred_at: datetime | None = None,
    ):
        self.source_id = source_id
        self.name = name
        self.domain = domain
        self.occurred_at = occurred_at or _utcnow()


@dataclass
class DocumentCollected:
    """Event fired when a document is collected from a source.

    Attributes:
        document_id: ID of the collected document
        source_id: ID of the source
        url: Document URL
        occurred_at: Event timestamp
    """

    document_id: UUID
    source_id: UUID
    url: str
    occurred_at: datetime

    def __init__(
        self,
        document_id: UUID,
        source_id: UUID,
        url: str,
        occurred_at: datetime | None = None,
    ):
        self.document_id = document_id
        self.source_id = source_id
        self.url = url
        self.occurred_at = occurred_at or _utcnow()


@dataclass
class InsightExtracted:
    """Event fired when an insight is extracted from a document.

    Attributes:
        insight_id: ID of the extracted insight
        document_id: ID of the source document
        confidence: Confidence score
        domain_tags: Domain classification tags
        occurred_at: Event timestamp
    """

    insight_id: UUID
    document_id: UUID
    confidence: float
    domain_tags: list[str]
    occurred_at: datetime

    def __init__(
        self,
        insight_id: UUID,
        document_id: UUID,
        confidence: float,
        domain_tags: list[str],
        occurred_at: datetime | None = None,
    ):
        self.insight_id = insight_id
        self.document_id = document_id
        self.confidence = confidence
        self.domain_tags = domain_tags
        self.occurred_at = occurred_at or _utcnow()


@dataclass
class ParsingFailed:
    """Event fired when document parsing fails.

    Attributes:
        document_id: ID of the failed document
        reason: Failure reason
        occurred_at: Event timestamp
    """

    document_id: UUID
    reason: str
    occurred_at: datetime

    def __init__(
        self,
        document_id: UUID,
        reason: str,
        occurred_at: datetime | None = None,
    ):
        self.document_id = document_id
        self.reason = reason
        self.occurred_at = occurred_at or _utcnow()
