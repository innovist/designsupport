"""Trend Knowledge application ports.

Port interfaces for external dependencies.
Implementations are provided in infrastructure layer.
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

# Import domain entities for type annotations
from apps.trend_knowledge.domain.entities import (
    TrendSource,
    TrendDocument,
    TrendInsight,
    TrendTaxonomy,
    ParsingFailureQueue,
)


class TrendSourceRepositoryPort(ABC):
    """Repository port for TrendSource entities."""

    @abstractmethod
    async def save(self, source: "TrendSource") -> TrendSource:
        """Save a trend source."""
        pass

    @abstractmethod
    async def get_by_id(self, source_id: UUID) -> "TrendSource | None":
        """Get source by ID."""
        pass

    @abstractmethod
    async def list_active(
        self,
        domain: str | None = None,
        limit: int = 100,
    ) -> list["TrendSource"]:
        """List active sources, optionally filtered by domain."""
        pass

    @abstractmethod
    async def update(self, source: "TrendSource") -> TrendSource:
        """Update an existing source."""
        pass


class TrendDocumentRepositoryPort(ABC):
    """Repository port for TrendDocument entities."""

    @abstractmethod
    async def save(self, document: "TrendDocument") -> "TrendDocument":
        """Save a trend document."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> "TrendDocument | None":
        """Get document by ID."""
        pass

    @abstractmethod
    async def list_by_source(
        self,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list["TrendDocument"]:
        """List documents by source ID."""
        pass

    @abstractmethod
    async def list_failed(
        self,
        limit: int = 50,
    ) -> list["TrendDocument"]:
        """List failed documents for retry."""
        pass

    @abstractmethod
    async def find_by_hash(self, content_hash: str) -> "TrendDocument | None":
        """Find document by content hash for deduplication."""
        pass


class TrendInsightRepositoryPort(ABC):
    """Repository port for TrendInsight entities."""

    @abstractmethod
    async def save(self, insight: "TrendInsight") -> "TrendInsight":
        """Save a trend insight."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        domain: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 10,
    ) -> list["TrendInsight"]:
        """Search insights by query text and filters."""
        pass

    @abstractmethod
    async def get_by_document(
        self,
        document_id: UUID,
    ) -> list["TrendInsight"]:
        """Get all insights for a document."""
        pass


class TrendTaxonomyRepositoryPort(ABC):
    """Repository port for TrendTaxonomy entities."""

    @abstractmethod
    async def save(self, taxonomy: "TrendTaxonomy") -> "TrendTaxonomy":
        """Save a taxonomy category."""
        pass

    @abstractmethod
    async def list_active(
        self,
        domain: str | None = None,
    ) -> list["TrendTaxonomy"]:
        """List active taxonomy categories, optionally by domain."""
        pass

    @abstractmethod
    async def get_by_id(self, taxonomy_id: UUID) -> "TrendTaxonomy | None":
        """Get taxonomy by ID."""
        pass


class ParsingFailureQueueRepositoryPort(ABC):
    """Repository port for ParsingFailureQueue entities."""

    @abstractmethod
    async def save(self, failure: "ParsingFailureQueue") -> "ParsingFailureQueue":
        """Save a failure queue entry."""
        pass

    @abstractmethod
    async def list_pending(
        self,
        limit: int = 50,
    ) -> list["ParsingFailureQueue"]:
        """List pending failures for retry."""
        pass

    @abstractmethod
    async def delete(self, failure_id: UUID) -> None:
        """Delete a failure queue entry."""
        pass


# Import RAGPort from shared infrastructure
from shared.infrastructure.rag_port_adapter import RAGPort


class CrawlerPort(ABC):
    """Port for web crawling operations.

    Abstract interface for Scrapy/Crawlee/Crawl4AI/Scrapling.
    """

    @abstractmethod
    async def crawl_url(
        self,
        url: str,
        source_id: UUID,
    ) -> tuple[str, str, str]:
        """Crawl a single URL.

        Args:
            url: URL to crawl
            source_id: Source ID for tracking

        Returns:
            Tuple of (title, content_text, raw_storage_uri)
        """
        pass

    @abstractmethod
    async def crawl_source(
        self,
        source: "TrendSource",
    ) -> list[tuple[str, str, str]]:
        """Crawl all URLs from a source.

        Args:
            source: TrendSource to crawl

        Returns:
            List of (title, content_text, raw_storage_uri) tuples
        """
        pass


class ParserPort(ABC):
    """Port for file parsing operations.

    Abstract interface for Magika/PDF/kordoc/rhwp parsers.
    """

    @abstractmethod
    async def parse_file(
        self,
        file_path: str,
        file_type: str | None = None,
    ) -> str:
        """Parse a file and extract text content.

        Args:
            file_path: Path to file to parse
            file_type: Optional file type hint (detected via Magika if None)

        Returns:
            Extracted text content

        Raises:
            ParsingError: If parsing fails
        """
        pass

    @abstractmethod
    async def detect_type(
        self,
        file_path: str,
    ) -> str:
        """Detect file type using Magika.

        Args:
            file_path: Path to file

        Returns:
            Detected file type (pdf, hwp, docx, etc.)
        """
        pass


class ModelPort(ABC):
    """Port for model operations.

    Delegates to ModelRouter (SPEC-04) with functional keys.
    """

    @abstractmethod
    async def extract_insights(
        self,
        document_text: str,
        domain: str,
    ) -> list[dict[str, Any]]:
        """Extract insights from document text.

        Uses ModelRouter with 'TrendResearch' functional key.

        Args:
            document_text: Document text content
            domain: Domain category

        Returns:
            List of insights with summary, keywords, evidence_quote
        """
        pass

    @abstractmethod
    async def summarize(
        self,
        text: str,
        max_length: int = 500,
    ) -> str:
        """Summarize text content.

        Args:
            text: Text to summarize
            max_length: Maximum summary length

        Returns:
            Summary text
        """
        pass


__all__ = [
    "TrendSourceRepositoryPort",
    "TrendDocumentRepositoryPort",
    "TrendInsightRepositoryPort",
    "TrendTaxonomyRepositoryPort",
    "ParsingFailureQueueRepositoryPort",
    "RAGPort",
    "CrawlerPort",
    "ParserPort",
    "ModelPort",
]
