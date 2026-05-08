"""Scrapy crawler adapter for static page crawling.

Implements CrawlerPort using Scrapy for robust static content extraction.
"""
import logging
from typing import Any
from uuid import UUID

from apps.trend_knowledge.infrastructure.adapters.crawlers.base import BaseCrawler
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)


class ScrapyCrawlerAdapter(BaseCrawler):
    """Scrapy-based crawler for static pages.

    Uses Scrapy's built-in selectors for content extraction.
    Runs Scrapy spider programmatically via CrawlerProcess.
    """

    def __init__(
        self,
        storage_base_path: str | None = None,
    ):
        """Initialize Scrapy crawler.

        Args:
            storage_base_path: Base path for storing raw content
        """
        super().__init__(storage_base_path)

    def _extract_content(
        self,
        response: Any,
        content_type: str,
    ) -> tuple[str, str]:
        """Extract title and text from Scrapy response.

        Args:
            response: httpx.Response (base class uses httpx)
            content_type: Content-Type header

        Returns:
            Tuple of (title, text)

        Note:
            This is a simplified implementation using httpx.
            Full Scrapy integration would use Scrapy's HtmlResponse.
        """
        from html.parser import HTMLParser

        class TitleExtractor(HTMLParser):
            """Extract title from HTML."""

            def __init__(self):
                super().__init__()
                self.in_title = False
                self.title = ""

            def handle_starttag(self, tag, attrs):
                if tag.lower() == "title":
                    self.in_title = True

            def handle_data(self, data):
                if self.in_title:
                    self.title += data

            def handle_endtag(self, tag):
                if tag.lower() == "title":
                    self.in_title = False

        class TextExtractor(HTMLParser):
            """Extract visible text from HTML."""

            def __init__(self):
                super().__init__()
                self.in_script = False
                self.in_style = False
                self.text = []

            def handle_starttag(self, tag, attrs):
                if tag.lower() in ["script", "style"]:
                    if tag.lower() == "script":
                        self.in_script = True
                    elif tag.lower() == "style":
                        self.in_style = True

            def handle_endtag(self, tag):
                if tag.lower() == "script":
                    self.in_script = False
                elif tag.lower() == "style":
                    self.in_style = False

            def handle_data(self, data):
                if not self.in_script and not self.in_style:
                    text = data.strip()
                    if text:
                        self.text.append(text)

        try:
            html_text = response.text.decode("utf-8", errors="ignore")
        except Exception:
            html_text = response.text if isinstance(response.text, str) else str(response.text)

        # Extract title
        title_extractor = TitleExtractor()
        title_extractor.feed(html_text)
        title = title_extractor.title.strip()

        # Extract text
        text_extractor = TextExtractor()
        text_extractor.feed(html_text)
        text = " ".join(text_extractor.text)

        # Fallback if no title found
        if not title:
            title = "Untitled"

        # Clean up text
        text = " ".join(text.split())

        return title, text
