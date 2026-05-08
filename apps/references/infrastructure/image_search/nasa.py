"""NASA Images image search adapter.

NASA Images API: https://images-api.nasa.gov
License: Public Domain (US government work)
Tier: 1
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter

logger = getLogger(__name__)


class NasaAdapter(ImageSearchAdapter):
    """NASA Images image search adapter.

    API Documentation: https://images.nasa.gov/docs/index.html
    No API key required (public domain data)
    """

    BASE_URL = "https://images-api.nasa.gov"
    TIER = 1

    def __init__(self):
        """Initialize NASA adapter."""
        super().__init__(provider_id="nasa", tier=self.TIER)

    def is_available(self) -> bool:
        """NASA API is always available (no API key needed)."""
        return True

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search NASA Images for media.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (year, center, etc.)

        Returns:
            List of normalized reference cards
        """
        # Build request parameters
        params = {
            "q": query,
            "media_type": "image",
            "page_size": min(count, 100),
        }

        # Add optional filters
        if options:
            if "year" in options:
                params["year"] = options["year"]
            if "center" in options:
                params["center"] = options["center"]

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            items = data.get("collection", {}).get("items", [])

            for item in items:
                card = self._normalize_nasa_item(item)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"NASA API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"NASA search failed: {e}")
            raise

    def _normalize_nasa_item(
        self,
        item: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize NASA item data to standard card format.

        Args:
            item: NASA item object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            title = item.get("data", [{}])[0].get("title")
            description = item.get("data", [{}])[0].get("description")
            center = item.get("data", [{}])[0].get("center")

            # Extract date created
            date_created_str = item.get("data", [{}])[0].get("date_created")
            published_at = None
            if date_created_str:
                try:
                    published_at = datetime.fromisoformat(
                        date_created_str.replace("Z", "+00:00"),
                    )
                except ValueError:
                    pass

            # Extract links
            links = item.get("links", [])
            if not links:
                return None

            # Find the largest image
            source_url = None
            for link in reversed(links):  # Start from largest
                if link.get("render") == "image":
                    source_url = link.get("href")
                    break

            # Find thumbnail
            thumbnail_url = None
            for link in links:
                if link.get("rel") == "preview":
                    thumbnail_url = link.get("href")
                    break

            if not source_url:
                return None

            # Fallback to source URL for thumbnail if no preview
            if not thumbnail_url:
                thumbnail_url = source_url

            # Build external URL
            nasa_id = item.get("data", [{}])[0].get("nasa_id")
            external_url = f"https://images.nasa.gov/details-{nasa_id}" if nasa_id else ""

            # Build domain tags from keywords
            keywords = item.get("data", [{}])[0].get("keywords", [])
            domain_tags = [kw.lower() for kw in keywords if kw] if keywords else []

            return NormalizedReferenceCard(
                provider="nasa",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=center or "NASA",
                license_id="PUBLIC-DOMAIN",
                attribution_text=f"{title if title else 'Image'}, NASA, Public Domain",
                license_url="https://www.nasa.gov/multimedia/guidelines/index.html",
                domain_tags=domain_tags,
                published_at=published_at,
                collected_at=datetime.now(timezone.utc),
                raw_meta=item,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize NASA item: {e}")
            return None
