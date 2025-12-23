"""
SearXNG search crawler
"""

from datetime import datetime
import hashlib
import html
import re
from typing import List, Optional, Dict, Any

import httpx
from dateutil import parser as date_parser

from app.core.config import get_settings
from .base_crawler import BaseCrawler, CrawledItem


class SearxngCrawler(BaseCrawler):
    """SearXNG search results crawler"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        settings = get_settings()
        config = config or {}
        self.base_url = (config.get("base_url") or settings.searxng_api_url or "").rstrip("/")
        self.language = config.get("language") or settings.default_language
        self.categories = config.get("categories") or "news"
        self.timeout_seconds = config.get("timeout_seconds") or settings.crawler_timeout_seconds or 30

    def get_channel_name(self) -> str:
        return "SearXNG"

    def supports_date_range(self) -> bool:
        return False

    def is_valid_item(self, item: CrawledItem) -> bool:
        if not item.url:
            return False
        content_length = len(item.content or "")
        return content_length >= 20

    async def crawl(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        if not self.base_url:
            raise ValueError("SEARXNG_API_URL not configured")

        results: List[CrawledItem] = []
        page = 1
        page_limit = max(1, (self.max_items + 9) // 10)
        endpoint = f"{self.base_url}/search"
        params = {
            "q": keyword,
            "format": "json",
            "language": self.language,
            "categories": self.categories
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            while len(results) < self.max_items and page <= page_limit:
                params["pageno"] = page
                response = await client.get(endpoint, params=params)
                if response.status_code != 200:
                    raise ValueError(f"SearXNG response error: {response.status_code}")
                payload = response.json()
                items = payload.get("results", [])
                if not items:
                    break
                for item in items:
                    if len(results) >= self.max_items:
                        break
                    crawled = self._to_crawled_item(item, start_date, end_date)
                    if crawled:
                        results.append(crawled)
                page += 1

        return results

    def _to_crawled_item(
        self,
        item: Dict[str, Any],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Optional[CrawledItem]:
        url = item.get("url") or ""
        if not url:
            return None
        published = self._parse_date(item.get("publishedDate") or item.get("published_date"))
        if start_date and published and published < start_date:
            return None
        if end_date and published and published > end_date:
            return None

        title = self._strip_html(item.get("title") or "")
        content = self._strip_html(item.get("content") or item.get("snippet") or "")
        source_id = self._hash_url(url)

        return CrawledItem(
            title=title,
            content=content,
            url=url,
            date=published,
            platform="searxng",
            source_id=source_id,
            metadata={
                "engine": item.get("engine"),
                "score": item.get("score"),
                "template": item.get("template")
            }
        )

    def _parse_date(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return date_parser.parse(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _hash_url(url: str) -> str:
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    @staticmethod
    def _strip_html(value: str) -> str:
        if not value:
            return ""
        cleaned = re.sub(r"<[^>]+>", " ", value)
        return html.unescape(" ".join(cleaned.split()))
