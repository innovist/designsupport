"""Base crawler adapter with common functionality.

Provides robots.txt checking, SSRF validation, and storage integration.
"""
import hashlib
import logging
from typing import Any
from uuid import UUID
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

import httpx

from apps.trend_knowledge.application.ports import CrawlerPort
from apps.trend_knowledge.domain.entities import TrendSource
from shared.domain.exceptions import OperationError
from shared.infrastructure.ssrf_guard.guard import SSRF_GUARD

logger = logging.getLogger(__name__)


class BaseCrawler(CrawlerPort):
    """Abstract base crawler with common httpx logic.

    Implements robots.txt checking and SSRF protection.
    """

    # Default user agent
    USER_AGENT = "MoAI-TrendBot/1.0 (+https://moai.ai/bot)"

    # Request timeout (seconds)
    TIMEOUT = 30.0

    def __init__(
        self,
        storage_base_path: str | None = None,
    ):
        """Initialize base crawler.

        Args:
            storage_base_path: Base path for storing raw content
        """
        self.storage_base_path = storage_base_path or "/tmp/trend_knowledge/raw"
        self._robots_cache: dict[str, RobotFileParser] = {}

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

        Raises:
            OperationError: If crawling fails
        """
        # Validate URL against SSRF guard
        try:
            validated_url = SSRF_GUARD.validate_url(url)
        except Exception as e:
            raise OperationError("BaseCrawler", f"SSRF validation failed: {e}")

        # Check robots.txt
        if not await self._check_robots_txt(validated_url):
            raise OperationError(
                "BaseCrawler",
                f"Robots.txt disallows crawling: {validated_url}",
            )

        # Fetch content
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(
                    validated_url,
                    headers={
                        "User-Agent": self.USER_AGENT,
                    },
                    follow_redirects=True,
                )
                response.raise_for_status()

                # Extract content
                content_type = response.headers.get("content-type", "")
                title, text = self._extract_content(response, content_type)

                # Store raw content
                raw_uri = await self._store_raw_content(
                    source_id,
                    validated_url,
                    response.content,
                )

                logger.info(f"Crawled URL: {validated_url} -> {raw_uri}")
                return title, text, raw_uri

        except httpx.HTTPStatusError as e:
            raise OperationError(
                "BaseCrawler",
                f"HTTP error {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            raise OperationError("BaseCrawler", f"Crawling failed: {e}")

    async def crawl_source(
        self,
        source: TrendSource,
    ) -> list[tuple[str, str, str]]:
        """Crawl all URLs from a source.

        Args:
            source: TrendSource to crawl

        Returns:
            List of (title, content_text, raw_storage_uri) tuples

        Raises:
            OperationError: If crawling fails
        """
        # For URL-based sources, crawl the single URL
        # For feed/API sources, this would be extended to fetch multiple URLs
        results = []

        try:
            title, text, raw_uri = await self.crawl_url(source.url, source.id)
            results.append((title, text, raw_uri))

        except OperationError as e:
            logger.error(f"Failed to crawl source {source.id}: {e}")
            raise

        return results

    async def _check_robots_txt(self, url: str) -> bool:
        """Check if robots.txt allows crawling.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Check cache
            if base_url in self._robots_cache:
                rp = self._robots_cache[base_url]
            else:
                # Fetch robots.txt
                robots_url = f"{base_url}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)

                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(
                            robots_url,
                            headers={"User-Agent": self.USER_AGENT},
                        )
                        if response.status_code == 200:
                            rp.parse(response.text.splitlines())
                        else:
                            # No robots.txt or error - allow crawling
                            rp = None
                except Exception:
                    # Failed to fetch robots.txt - allow crawling
                    rp = None

                self._robots_cache[base_url] = rp if rp else True

            # Check if allowed
            if rp is True or rp is None:
                return True
            return rp.can_fetch(self.USER_AGENT, url)

        except Exception as e:
            logger.warning(f"Failed to check robots.txt for {url}: {e}")
            # Allow crawling on error
            return True

    def _extract_content(
        self,
        response: httpx.Response,
        content_type: str,
    ) -> tuple[str, str]:
        """Extract title and text from response.

        Args:
            response: HTTP response
            content_type: Content-Type header

        Returns:
            Tuple of (title, text)

        Raises:
            NotImplementedError: Subclass must implement
        """
        raise NotImplementedError("Subclass must implement _extract_content")

    async def _store_raw_content(
        self,
        source_id: UUID,
        url: str,
        content: bytes,
    ) -> str:
        """Store raw content to object storage.

        Args:
            source_id: Source ID
            url: URL being crawled
            content: Raw content bytes

        Returns:
            Storage URI
        """
        import os
        from datetime import datetime, timezone

        # Create storage directory
        os.makedirs(self.storage_base_path, exist_ok=True)

        # Generate filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        filename = f"{source_id}_{timestamp}_{url_hash}.raw"

        # Store file
        file_path = os.path.join(self.storage_base_path, filename)
        with open(file_path, "wb") as f:
            f.write(content)

        # Return storage URI (file:// scheme for local storage)
        return f"file://{file_path}"
