"""Crawl4AI crawler adapter stub.

Implements CrawlerPort using Crawl4AI for LLM-ready Markdown extraction.
This is a stub - actual implementation requires crawl4ai package.

REQ-02-CRAWL-004: LLM-ready Markdown extraction via Crawl4AI.

To use this adapter:
1. Install crawl4ai: pip install crawl4ai
2. Implement crawl_url() using AsyncWebCrawler
3. Update CrawlerPort factory to return Crawl4AICrawlerAdapter

Reference: https://github.com/unclecode/crawl4ai
"""
import logging
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import CrawlerPort
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)


class Crawl4AICrawlerAdapter(CrawlerPort):
    """Crawl4AI-based crawler for LLM-ready content.

    Crawl4AI provides:
    - Markdown-formatted extraction optimized for LLMs
    - JavaScript rendering via Playwright
    - Clean text extraction without boilerplate
    - Screenshot and media extraction

    This is a stub implementation.
    """

    def __init__(
        self,
        storage_base_path: str | None = None,
        bypass_cache: bool = False,
        word_count_threshold: int = 10,
    ):
        """Initialize Crawl4AI crawler.

        Args:
            storage_base_path: Base path for storing raw content
            bypass_cache: Bypass Crawl4AI's caching mechanism
            word_count_threshold: Minimum word count for content extraction
        """
        self.storage_base_path = storage_base_path or "/tmp/trend_knowledge/raw"
        self.bypass_cache = bypass_cache
        self.word_count_threshold = word_count_threshold
        logger.warning(
            "Crawl4AICrawlerAdapter is a stub. "
            "Install crawl4ai to use this adapter: pip install crawl4ai"
        )

    async def crawl_url(
        self,
        url: str,
        source_id: UUID,
    ) -> tuple[str, str, str]:
        """Crawl a single URL using Crawl4AI.

        Args:
            url: URL to crawl
            source_id: Source ID for tracking

        Returns:
            Tuple of (title, markdown_text, raw_storage_uri)

        Raises:
            NotImplementedError: Until crawl4ai is installed
        """
        raise NotImplementedError(
            "Crawl4AICrawlerAdapter requires crawl4ai package. "
            "Install with: pip install crawl4ai\n"
            "Then implement using AsyncWebCrawler for Markdown extraction.\n"
            "Reference: https://github.com/unclecode/crawl4ai"
        )

    async def crawl_source(
        self,
        source: Any,  # TrendSource (avoiding circular import)
    ) -> list[tuple[str, str, str]]:
        """Crawl all URLs from a source using Crawl4AI.

        Args:
            source: TrendSource to crawl

        Returns:
            List of (title, markdown_text, raw_storage_uri) tuples

        Raises:
            NotImplementedError: Until crawl4ai is installed
        """
        raise NotImplementedError(
            "Crawl4AICrawlerAdapter requires crawl4ai package. "
            "Install with: pip install crawl4ai\n"
            "Then implement using AsyncWebCrawler in batch mode.\n"
            "Reference: https://github.com/unclecode/crawl4ai"
        )
