"""Pixabay image search adapter.

Pixabay API: https://pixabay.com/api/
License: Pixabay Content License (free to use, no attribution required)
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


class PixabayAdapter(ImageSearchAdapter):
    """Pixabay image search adapter.

    API Documentation: https://pixabay.com/api/docs/
    Requires: PIXABAY_API_KEY environment variable
    """

    BASE_URL = "https://pixabay.com/api"
    TIER = 1

    def __init__(self):
        """Initialize Pixabay adapter."""
        api_key = self._get_env_key("PIXABAY_API_KEY")
        if not api_key:
            logger.warning("PIXABAY_API_KEY not configured")

        super().__init__(provider_id="pixabay", tier=self.TIER)

        self._api_key = api_key

    def is_available(self) -> bool:
        """Check if Pixabay API key is configured."""
        return bool(self._get_env_key("PIXABAY_API_KEY"))

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Pixabay for images.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (image_type, orientation, category, etc.)

        Returns:
            List of normalized reference cards
        """
        if not self.is_available():
            raise ValidationError("Pixabay API key not configured")

        # Build request parameters
        params = {
            "key": self._api_key,
            "q": query,
            "per_page": min(count, 200),  # Pixabay max per page is 200
            "safesearch": "true",
        }

        # Add optional filters
        if options:
            if "image_type" in options:
                params["image_type"] = options["image_type"]
            if "orientation" in options:
                params["orientation"] = options["orientation"]
            if "category" in options:
                params["category"] = options["category"]
            if "min_width" in options:
                params["min_width"] = options["min_width"]
            if "min_height" in options:
                params["min_height"] = options["min_height"]

        try:
            response = await self._client.get(
                self.BASE_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            for hit in data.get("hits", []):
                card = self._normalize_pixabay_hit(hit)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Pixabay API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Pixabay search failed: {e}")
            raise

    def _normalize_pixabay_hit(
        self,
        hit: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Pixabay hit data to standard card format.

        Args:
            hit: Pixabay hit object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            page_url = hit.get("page_url", "")
            webformat_url = hit.get("webformatURL", "")
            preview_url = hit.get("previewURL", "")

            if not all([page_url, webformat_url, preview_url]):
                logger.warning("Pixabay hit missing required URLs")
                return None

            # Extract user info
            user = hit.get("user")
            user_id = hit.get("user_id")

            # Extract tags
            tags_str = hit.get("tags", "")
            domain_tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

            return NormalizedReferenceCard(
                provider="pixabay",
                tier=self.TIER,
                external_url=page_url,
                source_url=webformat_url,
                thumbnail_url=preview_url,
                title=None,  # Pixabay doesn't provide titles
                author=user,
                license_id="Pixabay-Content-License",
                attribution_text=self._build_attribution_text(
                    author=user,
                    provider="Pixabay",
                ),
                license_url="https://pixabay.com/service/license/",
                domain_tags=domain_tags,
                published_at=None,  # Pixabay doesn't provide publish date
                collected_at=datetime.now(timezone.utc),
                raw_meta=hit,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Pixabay hit: {e}")
            return None
