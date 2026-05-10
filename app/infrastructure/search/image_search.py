"""
Image search client - delegates to the same search backend as web search.
"""

from app.infrastructure.search.web_search import get_search_client
from app.application.ports.search_client import SearchClient


def get_image_search_client() -> SearchClient:
    """Return the same client as web search.

    SearXNG and Crawl4AI backends natively support image search.
    ExternalCrawlerSearchClient performs best-effort image search via web API.
    """
    return get_search_client()
