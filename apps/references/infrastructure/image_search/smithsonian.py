"""Smithsonian Open Access image search adapter.

Smithsonian API: https://api.si.edu/openaccess/api/v1.0
License: CC0-1.0 for Open Access items
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


class SmithsonianAdapter(ImageSearchAdapter):
    """Smithsonian Open Access image search adapter.

    API Documentation: https://edan.si.edu/openaccess/apidocs/
    Requires: SMITHSONIAN_API_KEY environment variable
    """

    BASE_URL = "https://api.si.edu/openaccess/api/v1.0"
    TIER = 1

    def __init__(self):
        """Initialize Smithsonian adapter."""
        api_key = self._get_env_key("SMITHSONIAN_API_KEY")
        if not api_key:
            logger.warning("SMITHSONIAN_API_KEY not configured")

        super().__init__(provider_id="smithsonian", tier=self.TIER)

        self._api_key = api_key

    def is_available(self) -> bool:
        """Check if Smithsonian API key is configured."""
        return bool(self._get_env_key("SMITHSONIAN_API_KEY"))

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Smithsonian Open Access for media.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options

        Returns:
            List of normalized reference cards
        """
        if not self.is_available():
            raise ValidationError("Smithsonian API key not configured")

        # Build request parameters
        params = {
            "api_key": self._api_key,
            "q": query,
            "rows": min(count, 100),
        }

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            rows = data.get("response", {}).get("rows", [])

            for row in rows:
                card = self._normalize_smithsonian_row(row)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Smithsonian API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Smithsonian search failed: {e}")
            raise

    def _normalize_smithsonian_row(
        self,
        row: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Smithsonian row data to standard card format.

        Args:
            row: Smithsonian row object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            title = row.get("title")
            content = row.get("content", {})
            descriptive_line = content.get("descriptiveNonRefiningFields", {})
            author = descriptive_line.get("name")

            # Extract URLs
            external_url = row.get("id", "")
            media = content.get("media", {})
            source_url = media.get("content", "")

            if not all([external_url, source_url]):
                return None

            # Use source URL as thumbnail (Smithsonian doesn't provide separate)
            thumbnail_url = source_url

            return NormalizedReferenceCard(
                provider="smithsonian",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=author,
                license_id="CC0-1.0",
                attribution_text=self._build_attribution_text(
                    author=author,
                    provider="Smithsonian",
                ),
                license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                domain_tags=[],
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta=row,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Smithsonian row: {e}")
            return None
