"""Crawl source use case.

Dispatches to appropriate crawler based on source configuration.
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any
from uuid import UUID, uuid4

from apps.trend_knowledge.application.ports import (
    CrawlerPort,
    TrendDocumentRepositoryPort,
    TrendSourceRepositoryPort,
)
from apps.trend_knowledge.domain.entities import TrendDocument, TrendDocumentStatus
from shared.domain.exceptions import OperationError

logger = getLogger(__name__)


class CrawlSourceUseCase:
    """Crawl trend source and save raw documents."""

    def __init__(
        self,
        source_repository: TrendSourceRepositoryPort,
        document_repository: TrendDocumentRepositoryPort,
        crawler_port: CrawlerPort,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            source_repository: Repository for source lookup
            document_repository: Repository for document persistence
            crawler_port: Crawler interface for web scraping
        """
        self._source_repository = source_repository
        self._document_repository = document_repository
        self._crawler_port = crawler_port

    async def execute(self, source_id: UUID) -> list[dict[str, Any]]:
        """Crawl a source and save discovered documents.

        Args:
            source_id: ID of the source to crawl

        Returns:
            List of created document metadata

        Raises:
            ValueError: If source not found or inactive
            OperationError: If crawling fails
        """
        # Load source
        source = await self._source_repository.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Source not found: {source_id}")

        if not source.is_active:
            raise ValueError(f"Source is inactive: {source_id}")

        logger.info(f"Crawling source: {source.url} (type: {source.source_type.value})")

        try:
            # Dispatch to crawler based on source type
            if source.source_type.value == "scrape":
                results = await self._crawler_port.crawl_source(source)
            elif source.source_type.value == "rss":
                # RSS feeds use specialized crawler (future implementation)
                results = await self._crawler_port.crawl_source(source)
            elif source.source_type.value == "api":
                # API sources use specialized crawler (future implementation)
                results = await self._crawler_port.crawl_source(source)
            else:
                raise ValueError(f"Unsupported source type: {source.source_type.value}")

            # Save documents
            created_docs = []
            for title, content_text, raw_storage_uri in results:
                # Check for duplicates via content hash
                import hashlib
                content_hash = hashlib.sha256(content_text.encode()).hexdigest()

                existing = await self._document_repository.find_by_hash(content_hash)
                if existing:
                    logger.debug(f"Duplicate document skipped: {existing.id}")
                    continue

                # Create document
                document = TrendDocument(
                    id=uuid4(),
                    source_id=source.id,
                    title=title,
                    raw_storage_uri=raw_storage_uri,
                    content_hash=content_hash,
                    status=TrendDocumentStatus.RAW,
                    created_at=datetime.now(timezone.utc),
                )

                saved_doc = await self._document_repository.save(document)
                created_docs.append({
                    "id": str(saved_doc.id),
                    "title": saved_doc.title,
                    "status": saved_doc.status.value,
                })

            logger.info(f"Crawled {len(created_docs)} new documents from {source.url}")
            return created_docs

        except Exception as e:
            logger.error(f"Crawling failed for source {source_id}: {e}")
            raise OperationError(f"Crawling failed: {e}") from e
