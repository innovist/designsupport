"""Openverse (formerly CC Search) image search adapter.

Openverse API: https://api.openverse.org/v1/
License: Varies (CC licenses) - extracted per item
Tier: 1
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter

logger = getLogger(__name__)


class OpenverseAdapter(ImageSearchAdapter):
    """Openverse image search adapter.

    API Documentation: https://api.openverse.org/v1/
    No API key required for basic usage
    """

    BASE_URL = "https://api.openverse.org/v1"
    TIER = 1

    def __init__(self):
        """Initialize Openverse adapter."""
        super().__init__(provider_id="openverse", tier=self.TIER)

    def is_available(self) -> bool:
        """Openverse is always available (no API key needed for basic usage)."""
        return True

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Openverse for CC-licensed images.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (license, filters, etc.)

        Returns:
            List of normalized reference cards
        """
        # Build request parameters
        params = {
            "q": query,
            "page_size": min(count, 50),
        }

        # Add optional filters
        if options:
            if "license" in options:
                params["license"] = options["license"]
            if "mature" in options:
                params["mature"] = options["mature"]

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/images/",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            for result in data.get("results", []):
                card = self._normalize_openverse_result(result)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Openverse API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Openverse search failed: {e}")
            raise

    def _normalize_openverse_result(
        self,
        result: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Openverse result data to standard card format.

        Args:
            result: Openverse result object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract URLs
            external_url = result.get("foreign_landing_url", "")
            source_url = result.get("url", "")
            thumbnail_url = result.get("thumbnail", "")

            if not all([external_url, source_url, thumbnail_url]):
                logger.warning("Openverse result missing required URLs")
                return None

            # Extract title
            title = result.get("title")

            # Extract creator
            creator = result.get("creator")
            creator_url = result.get("creator_url")

            # Extract license information
            license_ = result.get("license", "")
            license_version = result.get("license_version", "")
            license_id = f"{license_}-{license_version}" if license_version else license_

            # Map to SPDX
            if not license_id or license_id.lower() == "cc0":
                license_id = "CC0-1.0"
            elif license_id.startswith("CC-BY"):
                license_id = license_id.upper().replace(" ", "-")

            license_url = result.get("license_url")

            # Build attribution text
            attribution = self._build_attribution_text(
                author=creator,
                provider="Openverse",
                license_name=license_id,
            )

            # Extract tags
            tags = result.get("tags", [])
            domain_tags = [tag.get("name", "").lower() for tag in tags if tag.get("name")]

            return NormalizedReferenceCard(
                provider="openverse",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=creator,
                license_id=license_id,
                attribution_text=attribution,
                license_url=license_url,
                domain_tags=domain_tags,
                published_at=None,  # Openverse doesn't provide publish date
                collected_at=datetime.now(timezone.utc),
                raw_meta=result,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Openverse result: {e}")
            return None
