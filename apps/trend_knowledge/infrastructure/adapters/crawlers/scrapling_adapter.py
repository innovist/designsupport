"""Scrapling crawler adapter stub.

Implements CrawlerPort using Scrapling for anti-bot protected sites.
This is a stub - actual implementation requires scrapling package.

REQ-02-CRAWL-004: Anti-bot bypass via Scrapling.

To use this adapter:
1. Install scrapling: pip install scrapling
2. Implement crawl_url() using FetchButton or PlaywrightFetcher
3. Update CrawlerPort factory to return ScraplingCrawlerAdapter

Reference: https://github.com/viperml/scrapling
"""
import logging
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import CrawlerPort
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)


class ScraplingCrawlerAdapter(CrawlerPort):
    """Scrapling-based crawler for anti-bot protected sites.

    Scrapling provides:
    - Stealth mode to bypass anti-bot protections
    - Cloudflare, DataDome, and similar protection bypass
    - Playwright integration for JavaScript rendering
    - Automatic retry and error handling

    This is a stub implementation.
    """

    def __init__(
        self,
        storage_base_path: str | None = None,
        stealth: bool = True,
        javascript: bool = True,
    ):
        """Initialize Scrapling crawler.

        Args:
            storage_base_path: Base path for storing raw content
            stealth: Enable stealth mode for anti-bot bypass
            javascript: Enable JavaScript execution
        """
        self.storage_base_path = storage_base_path or "/tmp/trend_knowledge/raw"
        self.stealth = stealth
        self.javascript = javascript
        logger.warning(
            "ScraplingCrawlerAdapter is a stub. "
            "Install scrapling to use this adapter: pip install scrapling"
        )

    async def crawl_url(
        self,
        url: str,
        source_id: UUID,
    ) -> tuple[str, str, str]:
        """Crawl a single URL using Scrapling.

        Args:
            url: URL to crawl
            source_id: Source ID for tracking

        Returns:
            Tuple of (title, content_text, raw_storage_uri)

        Raises:
            NotImplementedError: Until scrapling is installed
        """
        raise NotImplementedError(
            "ScraplingCrawlerAdapter requires scrapling package. "
            "Install with: pip install scrapling\n"
            "Then implement using FetchButton or PlaywrightFetcher.\n"
            "Reference: https://github.com/viperml/scrapling"
        )

    async def crawl_source(
        self,
        source: Any,  # TrendSource (avoiding circular import)
    ) -> list[tuple[str, str, str]]:
        """Crawl all URLs from a source using Scrapling.

        Args:
            source: TrendSource to crawl

        Returns:
            List of (title, content_text, raw_storage_uri) tuples

        Raises:
            NotImplementedError: Until scrapling is installed
        """
        raise NotImplementedError(
            "ScraplingCrawlerAdapter requires scrapling package. "
            "Install with: pip install scrapling\n"
            "Then implement using FetchButton for batch crawling.\n"
            "Reference: https://github.com/viperml/scrapling"
        )
