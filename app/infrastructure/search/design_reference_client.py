"""Design reference image search via Unsplash and Pexels APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DesignReferenceImage:
    """Normalized image result from any image API."""
    id: str
    source: str  # "unsplash" | "pexels" | "pixabay"
    title: str
    image_url: str  # full-size image
    thumbnail_url: str  # small thumbnail for grid
    photographer: str
    source_url: str  # link to original page
    width: int = 0
    height: int = 0


class DesignReferenceClient:
    """Searches Unsplash and Pexels for design reference images."""

    async def search(self, query: str, per_page: int = 10) -> list[DesignReferenceImage]:
        settings = get_settings()
        results: list[DesignReferenceImage] = []

        # Try Unsplash first
        if settings.unsplash_access_key:
            try:
                results = await self._search_unsplash(
                    settings.unsplash_access_key, query, per_page
                )
                if results:
                    return results
            except Exception as exc:
                logger.warning("Unsplash search failed: %s", exc)

        # Fallback to Pexels
        if settings.pexels_api_key:
            try:
                results = await self._search_pexels(
                    settings.pexels_api_key, query, per_page
                )
                if results:
                    return results
            except Exception as exc:
                logger.warning("Pexels search failed: %s", exc)

        # Fallback to Pixabay
        if settings.pixabay_api_key:
            try:
                results = await self._search_pixabay(
                    settings.pixabay_api_key, query, per_page
                )
            except Exception as exc:
                logger.warning("Pixabay search failed: %s", exc)

        return results

    async def _search_unsplash(self, api_key: str, query: str, per_page: int) -> list[DesignReferenceImage]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                headers={"Authorization": f"Client-ID {api_key}"},
                params={"query": query, "per_page": per_page, "orientation": "squarish"},
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append(DesignReferenceImage(
                id=f"unsplash-{item['id']}",
                source="unsplash",
                title=item.get("description") or item.get("alt_description") or "",
                image_url=item["urls"]["regular"],
                thumbnail_url=item["urls"]["small"],
                photographer=item.get("user", {}).get("name", ""),
                source_url=item.get("links", {}).get("html", ""),
                width=item.get("width", 0),
                height=item.get("height", 0),
            ))
        return results

    async def _search_pexels(self, api_key: str, query: str, per_page: int) -> list[DesignReferenceImage]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": api_key},
                params={"query": query, "per_page": per_page, "orientation": "square"},
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("photos", []):
            results.append(DesignReferenceImage(
                id=f"pexels-{item['id']}",
                source="pexels",
                title=item.get("alt", ""),
                image_url=item["src"]["large"],
                thumbnail_url=item["src"]["medium"],
                photographer=item.get("photographer", ""),
                source_url=item.get("url", ""),
                width=item.get("width", 0),
                height=item.get("height", 0),
            ))
        return results

    async def _search_pixabay(self, api_key: str, query: str, per_page: int) -> list[DesignReferenceImage]:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://pixabay.com/api/",
                params={"key": api_key, "q": query, "per_page": per_page, "image_type": "photo"},
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for item in data.get("hits", []):
            results.append(DesignReferenceImage(
                id=f"pixabay-{item['id']}",
                source="pixabay",
                title=item.get("tags", ""),
                image_url=item["largeImageURL"],
                thumbnail_url=item["webformatURL"],
                photographer=item.get("user", ""),
                source_url=item.get("pageURL", ""),
                width=item.get("imageWidth", 0),
                height=item.get("imageHeight", 0),
            ))
        return results


_client: DesignReferenceClient | None = None


def get_design_reference_client() -> DesignReferenceClient:
    global _client
    if _client is None:
        _client = DesignReferenceClient()
    return _client
