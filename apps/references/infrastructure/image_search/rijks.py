"""Rijksmuseum image search adapter.

Rijksmuseum API: https://www.rijksmuseum.nl/api/en
License: CC0-1.0 for most collection items
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


class RijksAdapter(ImageSearchAdapter):
    """Rijksmuseum image search adapter.

    API Documentation: https://www.rijksmuseum.nl/en/api
    Requires: RIJKS_API_KEY environment variable
    """

    BASE_URL = "https://www.rijksmuseum.nl/api/en"
    TIER = 1

    def __init__(self):
        """Initialize Rijksmuseum adapter."""
        api_key = self._get_env_key("RIJKS_API_KEY")
        if not api_key:
            logger.warning("RIJKS_API_KEY not configured")

        super().__init__(provider_id="rijks", tier=self.TIER)

        self._api_key = api_key

    def is_available(self) -> bool:
        """Check if Rijksmuseum API key is configured."""
        return bool(self._get_env_key("RIJKS_API_KEY"))

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Rijksmuseum collection for images.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options

        Returns:
            List of normalized reference cards
        """
        if not self.is_available():
            raise ValidationError("Rijksmuseum API key not configured")

        # Build request parameters
        params = {
            "key": self._api_key,
            "q": query,
            "ps": min(count, 100),
            "imgonly": "true",  # Only results with images
        }

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/collection",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            art_objects = data.get("artObjects", [])

            for obj in art_objects:
                card = self._normalize_rijks_object(obj)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Rijksmuseum API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Rijksmuseum search failed: {e}")
            raise

    def _normalize_rijks_object(
        self,
        obj: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Rijksmuseum object data to standard card format.

        Args:
            obj: Rijksmuseum art object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            title = obj.get("title")
            principal_maker = obj.get("principalMaker")
            external_url = obj.get("links", {}).get("web", "")

            # Extract image URL
            header_image = obj.get("headerImage", {})
            source_url = header_image.get("url")

            if not all([external_url, source_url]):
                return None

            # Use source URL as thumbnail
            thumbnail_url = source_url

            return NormalizedReferenceCard(
                provider="rijks",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=principal_maker,
                license_id="CC0-1.0",
                attribution_text=self._build_attribution_text(
                    author=principal_maker,
                    provider="Rijksmuseum",
                ),
                license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                domain_tags=[],
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta=obj,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Rijksmuseum object: {e}")
            return None
