"""Met Museum Open Access image search adapter.

Met Museum Collection API: https://collectionapi.metmuseum.org/public/collection/v1
License: CC0-1.0 for Open Access items
Tier: 1
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter

logger = getLogger(__name__)


class MetAdapter(ImageSearchAdapter):
    """Met Museum Open Access image search adapter.

    API Documentation: https://metmuseum.github.io/
    No API key required (public domain data)
    """

    BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"
    TIER = 1

    def __init__(self):
        """Initialize Met adapter."""
        super().__init__(provider_id="met", tier=self.TIER)

    def is_available(self) -> bool:
        """Met Museum API is always available (no API key needed)."""
        return True

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Met Museum collection for Open Access images.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (department, medium, etc.)

        Returns:
            List of normalized reference cards
        """
        # Step 1: Search for object IDs
        search_params = {
            "q": query,
            "hasImages": "true",
            "isHighlight": "false",
            "isPublicDomain": "true",  # Only Open Access items
        }

        try:
            # Search for object IDs
            search_response = await self._client.get(
                f"{self.BASE_URL}/search",
                params=search_params,
            )
            search_response.raise_for_status()
            search_data = search_response.json()

            object_ids = search_data.get("objectIDs", [])[:count]
            if not object_ids:
                return []

            # Step 2: Fetch details for each object
            results = []
            for object_id in object_ids:
                card = await self._fetch_met_object(object_id)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Met Museum API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Met Museum search failed: {e}")
            raise

    async def _fetch_met_object(
        self,
        object_id: int,
    ) -> NormalizedReferenceCard | None:
        """Fetch and normalize a single Met Museum object.

        Args:
            object_id: Met Museum object ID

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/objects/{object_id}",
            )
            response.raise_for_status()
            obj = response.json()

            # Check if object is public domain and has image
            if not obj.get("isPublicDomain"):
                return None

            primary_image = obj.get("primaryImage")
            if not primary_image:
                return None

            # Extract basic info
            title = obj.get("title")
            artist = obj.get("artistDisplayName")
            external_url = obj.get("objectURL")

            # Build attribution text
            attribution = f"{title}, The Metropolitan Museum of Art, CC0"

            # Extract domain tags from classification and department
            domain_tags = []
            classification = obj.get("classification", "").lower()
            department = obj.get("department", "").lower()
            if classification:
                domain_tags.append(classification)
            if department:
                domain_tags.append(department)

            return NormalizedReferenceCard(
                provider="met",
                tier=self.TIER,
                external_url=external_url,
                source_url=primary_image,
                thumbnail_url=primary_image,  # Met doesn't provide separate thumbnails
                title=title,
                author=artist,
                license_id="CC0-1.0",
                attribution_text=attribution,
                license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                domain_tags=domain_tags,
                published_at=None,  # Met doesn't provide publish date
                collected_at=datetime.now(timezone.utc),
                raw_meta=obj,
            )

        except Exception as e:
            logger.warning(f"Failed to fetch Met object {object_id}: {e}")
            return None
