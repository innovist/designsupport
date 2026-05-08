"""Pexels image search adapter.

Pexels API: https://api.pexels.com/v1
License: Pexels License (free to use, no attribution required)
Tier: 1
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter
from shared.domain.exceptions import ValidationError

logger = getLogger(__name__)


class PexelsAdapter(ImageSearchAdapter):
    """Pexels image search adapter.

    API Documentation: https://www.pexels.com/api/
    Requires: PEXELS_API_KEY environment variable
    """

    BASE_URL = "https://api.pexels.com/v1"
    TIER = 1

    def __init__(self):
        """Initialize Pexels adapter."""
        api_key = self._get_env_key("PEXELS_API_KEY")
        if not api_key:
            logger.warning("PEXELS_API_KEY not configured")

        super().__init__(provider_id="pexels", tier=self.TIER)

        # Update client headers with authorization
        if api_key:
            self._client.headers.update({
                "Authorization": api_key,
            })

    def is_available(self) -> bool:
        """Check if Pexels API key is configured."""
        return bool(self._get_env_key("PEXELS_API_KEY"))

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Pexels for photos.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (orientation, color, size, etc.)

        Returns:
            List of normalized reference cards
        """
        if not self.is_available():
            raise ValidationError("Pexels API key not configured")

        # Build request parameters
        params = {
            "query": query,
            "per_page": min(count, 80),  # Pexels max per page is 80
        }

        # Add optional filters
        if options:
            if "orientation" in options:
                params["orientation"] = options["orientation"]
            if "size" in options:
                params["size"] = options["size"]
            if "color" in options:
                params["color"] = options["color"]

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            for photo in data.get("photos", []):
                card = self._normalize_pexels_photo(photo)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Pexels API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Pexels search failed: {e}")
            raise

    def _normalize_pexels_photo(
        self,
        photo: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Pexels photo data to standard card format.

        Args:
            photo: Pexels photo object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            external_url = photo.get("url", "")
            photographer = photo.get("photographer")

            # Extract image URLs
            src = photo.get("src", {})
            source_url = src.get("large2x") or src.get("original", "")
            thumbnail_url = src.get("large", "")

            if not all([external_url, source_url, thumbnail_url]):
                logger.warning("Pexels photo missing required URLs")
                return None

            # Extract alt text
            alt = photo.get("alt", "")

            # Build domain tags from Pexels doesn't provide categories
            domain_tags = []

            return NormalizedReferenceCard(
                provider="pexels",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=alt,
                author=photographer,
                license_id="Pexels-License",
                attribution_text=self._build_attribution_text(
                    author=photographer,
                    provider="Pexels",
                ),
                license_url="https://www.pexels.com/license/",
                domain_tags=domain_tags,
                published_at=None,  # Pexels doesn't provide publish date
                collected_at=datetime.now(timezone.utc),
                raw_meta=photo,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Pexels photo: {e}")
            return None
