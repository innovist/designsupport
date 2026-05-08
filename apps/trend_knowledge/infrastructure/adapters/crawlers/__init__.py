"""Crawler adapters for web scraping.

Implements CrawlerPort interface with multiple crawler backends.
"""
from apps.trend_knowledge.infrastructure.adapters.crawlers.base import BaseCrawler
from apps.trend_knowledge.infrastructure.adapters.crawlers.crawl4ai_adapter import (
    Crawl4AICrawlerAdapter,
)
from apps.trend_knowledge.infrastructure.adapters.crawlers.crawlee_adapter import (
    CrawleeCrawlerAdapter,
)
from apps.trend_knowledge.infrastructure.adapters.crawlers.scrapling_adapter import (
    ScraplingCrawlerAdapter,
)
from apps.trend_knowledge.infrastructure.adapters.crawlers.scrapy_adapter import (
    ScrapyCrawlerAdapter,
)

__all__ = [
    "BaseCrawler",
    "ScrapyCrawlerAdapter",
    "CrawleeCrawlerAdapter",
    "Crawl4AICrawlerAdapter",
    "ScraplingCrawlerAdapter",
]
