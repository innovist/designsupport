"""
Web search clients: SearXNG, External Crawler API, Crawl4AI, or NoOp fallback.

Priority chain (controlled by SEARCH_BACKEND env var):
  crawl4ai -> external -> searxng -> noop
"""

from __future__ import annotations

import asyncio

from app.application.ports.search_client import SearchClient, WebSearchResult, ImageSearchResult
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


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


class ExternalCrawlerSearchClient(SearchClient):
    """Calls an external Django-based crawler API with built-in search engine integration.

    API protocol (from crawler_api_docs.md):
      Auth:   Token <token> (DRF TokenAuthentication)
      Start:  POST /api/crawlers/start/  {"source": [...], "keyword": [...], "limit": N}
      Sources: GET /api/crawlers/sources/  → ["bing", "duckduckgo", "google", "yahoo"]
      Status: GET /api/crawlers/status/?task_id=<id>  → result: "started|success|failure|revoked"
      Data:   GET /api/crawlers/data/?task_id=<id>&page=1&page_size=N
      Stop:   POST /api/crawlers/stop/  {"task_id": "<id>"}
      Webhook: WS /webhook/<task_id>/  (real-time updates)
    """

    DEFAULT_SOURCES = ["google", "duckduckgo"]
    FINAL_STATES = frozenset({"success", "failure", "revoked"})

    def __init__(self, base_url: str, token: str, poll_interval: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.poll_interval = poll_interval

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Token {self.token}"}

    async def web_search(self, query: str, num_results: int = 10) -> list[WebSearchResult]:
        import httpx

        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=120) as client:
            task_id = await self._start_search(client, headers, query, num_results)
            if not task_id:
                return []

            final_status = await self._poll_until_done(client, headers, task_id)
            if final_status != "success":
                return []

            raw_items = await self._fetch_data(client, headers, task_id, num_results)
            return _build_web_results(raw_items, num_results)

    async def image_search(self, query: str, num_results: int = 10) -> list[ImageSearchResult]:
        import httpx

        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=120) as client:
            task_id = await self._start_search(client, headers, query, num_results)
            if not task_id:
                return []

            final_status = await self._poll_until_done(client, headers, task_id)
            if final_status != "success":
                return []

            raw_items = await self._fetch_data(client, headers, task_id, num_results)
            return _build_image_results(raw_items, num_results)

    async def _start_image_search(
        self, client, headers: dict, query: str, limit: int
    ) -> str | None:
        try:
            resp = await client.post(
                f"{self.base_url}/api/crawlers/start/",
                headers=headers,
                json={
                    "source": ["google"],
                    "keyword": [f"{query} images"],
                    "limit": limit,
                },
            )
            if resp.status_code not in (200, 201, 202):
                return None
            body = resp.json()
            task_id = body.get("task_id")
            if not task_id:
                return None
            logger.info("External crawler image search started: task=%s query=%s", task_id, query[:50])
            return str(task_id)
        except Exception as exc:
            logger.warning("External crawler image start error: %s", exc)
            return None

    async def _start_search(
        self, client, headers: dict, query: str, limit: int
    ) -> str | None:
        try:
            resp = await client.post(
                f"{self.base_url}/api/crawlers/start/",
                headers=headers,
                json={
                    "source": self.DEFAULT_SOURCES,
                    "keyword": [query],
                    "limit": limit,
                },
            )
            if resp.status_code not in (200, 201, 202):
                logger.warning(
                    "External crawler start failed: %s %s",
                    resp.status_code, resp.text[:200],
                )
                return None
            body = resp.json()
            task_id = body.get("task_id")
            if not task_id:
                logger.warning("External crawler returned no task_id: %s", resp.text[:200])
                return None
            logger.info("External crawler search started: task=%s query=%s", task_id, query[:50])
            return str(task_id)
        except Exception as exc:
            logger.warning("External crawler start error: %s", exc)
            return None

    async def _poll_until_done(self, client, headers: dict, task_id: str) -> str:
        for attempt in range(20):
            await asyncio.sleep(self.poll_interval)
            try:
                resp = await client.get(
                    f"{self.base_url}/api/crawlers/status/",
                    params={"task_id": task_id},
                    headers=headers,
                )
                if resp.status_code != 200:
                    continue
                body = resp.json()
                result_val = str(body.get("result", ""))
                if result_val in self.FINAL_STATES:
                    if result_val != "success":
                        logger.warning("External crawler task %s ended: %s", task_id, result_val)
                    return result_val
            except Exception as exc:
                logger.debug("External crawler poll error (attempt %d): %s", attempt, exc)

        logger.warning("External crawler task %s timed out after 20 polls", task_id)
        await self._stop_task(client, headers, task_id)
        return "timeout"

    async def _stop_task(self, client, headers: dict, task_id: str) -> None:
        try:
            await client.post(
                f"{self.base_url}/api/crawlers/stop/",
                headers=headers,
                json={"task_id": task_id},
            )
        except Exception:
            pass

    async def _fetch_data(
        self, client, headers: dict, task_id: str, limit: int
    ) -> list[dict]:
        expanded_limit = limit * len(self.DEFAULT_SOURCES)
        try:
            resp = await client.get(
                f"{self.base_url}/api/crawlers/data/",
                params={"task_id": task_id, "page": 1, "page_size": expanded_limit},
                headers=headers,
            )
            if resp.status_code != 200:
                logger.warning("External crawler data fetch failed: %s", resp.status_code)
                return []
            body = resp.json()
            items = body.get("result", [])
            if isinstance(items, list):
                logger.info(
                    "External crawler returned %d items (total_count=%s) for task %s",
                    len(items), body.get("total_count"), task_id,
                )
                return items
        except Exception as exc:
            logger.warning("External crawler data error: %s", exc)
        return []


class Crawl4AISearchClient(SearchClient):
    """Calls Crawl4AI API for LLM-friendly search results."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def web_search(self, query: str, num_results: int = 10) -> list[WebSearchResult]:
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/crawl",
                    json={
                        "urls": [f"https://www.google.com/search?q={query}"],
                        "browser_config": {"type": "native"},
                        "crawler_config": {"type": "CSSOrTextExtractionStrategy"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data if isinstance(data, list) else [data]:
                    if isinstance(item, dict):
                        md = item.get("markdown", {})
                        raw = md.get("raw_content", "") if isinstance(md, dict) else str(md)
                        url = item.get("url", "")
                        results.append(WebSearchResult(
                            title=item.get("metadata", {}).get("title", "") if isinstance(item.get("metadata"), dict) else "",
                            url=url,
                            snippet=raw[:500] if raw else "",
                        ))
                    if len(results) >= num_results:
                        break
                return results
            except Exception as exc:
                logger.warning("Crawl4AI search failed: %s", exc)
        return []

    async def image_search(self, query: str, num_results: int = 10) -> list[ImageSearchResult]:
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/crawl",
                    json={
                        "urls": [f"https://www.google.com/search?q={query}&tbm=isch"],
                        "browser_config": {"type": "native"},
                        "crawler_config": {"type": "CSSOrTextExtractionStrategy"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data if isinstance(data, list) else [data]:
                    if isinstance(item, dict):
                        url = item.get("url", "")
                        results.append(ImageSearchResult(
                            title=item.get("metadata", {}).get("title", "") if isinstance(item.get("metadata"), dict) else "",
                            url=url,
                            image_url=item.get("metadata", {}).get("ogImage", url) if isinstance(item.get("metadata"), dict) else url,
                            source_domain=_extract_domain(url),
                        ))
                    if len(results) >= num_results:
                        break
                return results
            except Exception as exc:
                logger.warning("Crawl4AI image search failed: %s", exc)
        return []


class NoOpSearchClient(SearchClient):
    """Returns empty results when no search backend is configured."""

    async def web_search(self, query: str, num_results: int = 10) -> list[WebSearchResult]:  # noqa: ARG002
        logger.warning(
            "No search backend configured. Set SEARCH_BACKEND=searxng|external|crawl4ai "
            "and the corresponding URL in .env."
        )
        return []

    async def image_search(self, query: str, num_results: int = 10) -> list[ImageSearchResult]:  # noqa: ARG002
        logger.warning(
            "No search backend configured. Set SEARCH_BACKEND=searxng|external|crawl4ai "
            "and the corresponding URL in .env."
        )
        return []


# ---------------------------------------------------------------------------
# URL cleaning and flexible result builders
# ---------------------------------------------------------------------------

def _clean_url(raw_url: str) -> str:
    """Extract the real URL from search engine redirect URLs.

    Handles:
      - DuckDuckGo: //duckduckgo.com/l/?uddg=ENCODED_REAL_URL
      - Protocol-relative: //example.com/path → https://example.com/path
    """
    if not raw_url:
        return ""

    url = raw_url.strip()

    # DuckDuckGo redirect: extract uddg parameter
    if "duckduckgo.com/l/" in url and "uddg=" in url:
        from urllib.parse import parse_qs, urlparse
        try:
            parsed = urlparse(url if "://" in url else "https:" + url)
            params = parse_qs(parsed.query)
            encoded_urls = params.get("uddg", [])
            if encoded_urls:
                from urllib.parse import unquote
                cleaned = unquote(encoded_urls[0])
                if cleaned.startswith("http"):
                    return cleaned
        except Exception:
            pass

    # Protocol-relative URL: //example.com → https://example.com
    if url.startswith("//"):
        return "https:" + url

    return url


def _build_web_results(raw_items: list[dict], limit: int) -> list[WebSearchResult]:
    """Convert flexible dict structures into WebSearchResult.

    Handles various key names: title/name/heading, content/description/snippet/text, url/link/href.
    """
    results = []
    for item in raw_items[:limit]:
        if not isinstance(item, dict):
            continue
        title = _pick(item, "title", "name", "heading")
        raw_url = _pick(item, "url", "link", "href")
        url = _clean_url(raw_url)
        snippet = _pick(item, "content", "description", "snippet", "text")
        if isinstance(snippet, str):
            snippet = snippet[:500]
        elif snippet:
            snippet = str(snippet)[:500]
        else:
            snippet = ""
        published_date = _pick(item, "published_date", "publishedDate", "date")
        results.append(WebSearchResult(
            title=title, url=url, snippet=snippet,
            published_date=published_date or None,
        ))
    return results


def _build_image_results(raw_items: list[dict], limit: int) -> list[ImageSearchResult]:
    """Convert flexible dict structures into ImageSearchResult."""
    results = []
    for item in raw_items[:limit]:
        if not isinstance(item, dict):
            continue
        title = _pick(item, "title", "name", "heading")
        raw_url = _pick(item, "url", "link", "href")
        url = _clean_url(raw_url)
        image_url = _pick(item, "image_url", "img_src", "src", "thumbnail", "image") or url
        results.append(ImageSearchResult(
            title=title, url=url, image_url=image_url,
            source_domain=_extract_domain(url),
        ))
    return results


def _pick(d: dict, *keys: str) -> str:
    """Return the first non-empty value from dict for any of the given keys."""
    for k in keys:
        v = d.get(k)
        if v and isinstance(v, str):
            return v.strip()
        if v:
            return str(v).strip()
    return ""


def get_search_client() -> SearchClient:
    """Return the configured search client based on SEARCH_BACKEND setting.

    Calls get_settings() each time to respect runtime config changes.
    Priority: explicit setting > auto-detect from .env URLs > NoOp fallback.
    """
    s = get_settings()
    backend = s.search_backend.lower()

    # Explicit selection
    if backend == "crawl4ai" and s.crawl4ai_api_url:
        logger.info("Search backend: Crawl4AI (%s)", s.crawl4ai_api_url)
        return Crawl4AISearchClient(s.crawl4ai_api_url)

    if backend == "external" and s.web_search_crawler_api_base_url:
        logger.info("Search backend: External Crawler (%s)", s.web_search_crawler_api_base_url)
        return ExternalCrawlerSearchClient(
            base_url=s.web_search_crawler_api_base_url,
            token=s.web_search_crawler_api_token or "",
            poll_interval=s.web_search_crawler_api_poll_interval_seconds,
        )

    if backend == "searxng" and s.searxng_api_url:
        logger.info("Search backend: SearXNG (%s)", s.searxng_api_url)
        return SearXNGSearchClient(s.searxng_api_url)

    # Auto-detect: try external crawler first (already configured in .env)
    if s.web_search_crawler_api_base_url:
        logger.info(
            "Search backend: auto-detected External Crawler (%s)",
            s.web_search_crawler_api_base_url,
        )
        return ExternalCrawlerSearchClient(
            base_url=s.web_search_crawler_api_base_url,
            token=s.web_search_crawler_api_token or "",
            poll_interval=s.web_search_crawler_api_poll_interval_seconds,
        )

    if s.searxng_api_url:
        logger.info("Search backend: auto-detected SearXNG (%s)", s.searxng_api_url)
        return SearXNGSearchClient(s.searxng_api_url)

    logger.warning("No search backend configured. Pipeline search steps will return empty results.")
    return NoOpSearchClient()


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""
