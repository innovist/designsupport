"""
Web search client using SearXNG or returning empty results if not configured.
"""

from __future__ import annotations

from app.application.ports.search_client import SearchClient, WebSearchResult, ImageSearchResult
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SearXNGSearchClient(SearchClient):
    """Calls a local SearXNG instance for web and image search."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def web_search(self, query: str, num_results: int = 10) -> list[WebSearchResult]:
        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json", "engines": "google,bing"},
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", [])[:num_results]:
            results.append(WebSearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                published_date=item.get("publishedDate"),
            ))
        return results

    async def image_search(self, query: str, num_results: int = 10) -> list[ImageSearchResult]:
        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{self.base_url}/search",
                params={"q": query, "format": "json", "categories": "images"},
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("results", [])[:num_results]:
            results.append(ImageSearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                image_url=item.get("img_src", item.get("url", "")),
                source_domain=_extract_domain(item.get("url", "")),
            ))
        return results


class NoOpSearchClient(SearchClient):
    """Returns empty results when no search backend is configured."""

    async def web_search(self, query: str, num_results: int = 10) -> list[WebSearchResult]:  # noqa: ARG002
        logger.warning(
            "No search backend configured (set SEARXNG_API_URL). Returning empty results."
        )
        return []

    async def image_search(self, query: str, num_results: int = 10) -> list[ImageSearchResult]:  # noqa: ARG002
        logger.warning(
            "No search backend configured (set SEARXNG_API_URL). Returning empty results."
        )
        return []


def get_search_client() -> SearchClient:
    if settings.searxng_api_url:
        return SearXNGSearchClient(settings.searxng_api_url)
    return NoOpSearchClient()


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""
