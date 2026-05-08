"""Crawlee crawler adapter stub.

Implements CrawlerPort using Crawlee (previously Apify SDK) for Python.
This is a stub - actual implementation requires crawlee package.

REQ-02-CRAWL-003: Alternative crawler support (Crawlee, Crawl4AI, Scrapling).

To use this adapter:
1. Install crawlee: pip install crawlee
2. Implement crawl_url() using Crawlee's CheerioCrawler or PlaywrightCrawler
3. Update CrawlerPort factory to return CrawleeCrawlerAdapter

Reference: https://crawlee.dev/python/
"""
import logging
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import CrawlerPort
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)


class CrawleeCrawlerAdapter(CrawlerPort):
    """Crawlee-based crawler for modern web scraping.

    Crawlee (formerly Apify SDK) provides:
    - Automatic retries and error handling
    - Proxy rotation
    - Smart crawling with request queue
    - Headless browser support (Playwright/Puppeteer)

    This is a stub implementation.
    """

    def __init__(
        self,
        storage_base_path: str | None = None,
        headless: bool = True,
    ):
        """Initialize Crawlee crawler.

        Args:
            storage_base_path: Base path for storing raw content
            headless: Run browser in headless mode
        """
        self.storage_base_path = storage_base_path or "/tmp/trend_knowledge/raw"
        self.headless = headless
        logger.warning(
            "CrawleeCrawlerAdapter is a stub. "
            "Install crawlee to use this adapter: pip install crawlee"
        )

    async def crawl_url(
        self,
        url: str,
        source_id: UUID,
    ) -> tuple[str, str, str]:
        """Crawl a single URL using Crawlee.

        Args:
            url: URL to crawl
            source_id: Source ID for tracking

        Returns:
            Tuple of (title, content_text, raw_storage_uri)

        Raises:
            NotImplementedError: Until crawlee is installed
        """
        raise NotImplementedError(
            "CrawleeCrawlerAdapter requires crawlee package. "
            "Install with: pip install crawlee\n"
            "Then implement using Crawlee's CheerioCrawler or PlaywrightCrawler.\n"
            "Reference: https://crawlee.dev/python/docs/quick-start"
        )

    async def crawl_source(
        self,
        source: Any,  # TrendSource (avoiding circular import)
    ) -> list[tuple[str, str, str]]:
        """Crawl all URLs from a source using Crawlee.

        Args:
            source: TrendSource to crawl

        Returns:
            List of (title, content_text, raw_storage_uri) tuples

        Raises:
            NotImplementedError: Until crawlee is installed
        """
        raise NotImplementedError(
            "CrawleeCrawlerAdapter requires crawlee package. "
            "Install with: pip install crawlee\n"
            "Then implement using Crawlee's RequestQueue for multi-URL crawling.\n"
            "Reference: https://crawlee.dev/python/docs/examples/request-queue"
        )
