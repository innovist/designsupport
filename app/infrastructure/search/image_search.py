"""
Image search client - delegates to the same SearXNG backend.
"""

from app.infrastructure.search.web_search import NoOpSearchClient, SearXNGSearchClient, get_search_client
from app.application.ports.search_client import SearchClient


def get_image_search_client() -> SearchClient:
    """Return the same client as web search - SearXNG handles both."""
    return get_search_client()
