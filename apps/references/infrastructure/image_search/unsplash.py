"""Unsplash image search adapter.

Unsplash API: https://api.unsplash.com
License: Unsplash License (free to use, no attribution required but recommended)
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


class UnsplashAdapter(ImageSearchAdapter):
    """Unsplash image search adapter.

    API Documentation: https://unsplash.com/developers
    Requires: UNSPLASH_ACCESS_KEY environment variable
    """

    BASE_URL = "https://api.unsplash.com"
    TIER = 1

    def __init__(self):
        """Initialize Unsplash adapter."""
        access_key = self._get_env_key("UNSPLASH_ACCESS_KEY")
        if not access_key:
            logger.warning("UNSPLASH_ACCESS_KEY not configured")

        super().__init__(provider_id="unsplash", tier=self.TIER)

        # Update client headers with authorization
        if access_key:
            self._client.headers.update({
                "Authorization": f"Client-ID {access_key}",
            })

    def is_available(self) -> bool:
        """Check if Unsplash API key is configured."""
        return bool(self._get_env_key("UNSPLASH_ACCESS_KEY"))

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Unsplash for photos.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (orientation, color, etc.)

        Returns:
            List of normalized reference cards
        """
        if not self.is_available():
            raise ValidationError("Unsplash API key not configured")

        # Build request parameters
        params = {
            "query": query,
            "per_page": min(count, 30),  # Unsplash max per page is 30
        }

        # Add optional filters
        if options:
            if "orientation" in options:
                params["orientation"] = options["orientation"]
            if "color" in options:
                params["color"] = options["color"]

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search/photos",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            for photo in data.get("results", []):
                card = self._normalize_unsplash_photo(photo)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Unsplash API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Unsplash search failed: {e}")
            raise

    def _normalize_unsplash_photo(
        self,
        photo: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Unsplash photo data to standard card format.

        Args:
            photo: Unsplash photo object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            external_url = photo.get("links", {}).get("html", "")
            source_url = photo.get("urls", {}).get("regular", "")
            thumbnail_url = photo.get("urls", {}).get("small", "")

            if not all([external_url, source_url, thumbnail_url]):
                logger.warning("Unsplash photo missing required URLs")
                return None

            # Extract author info
            user = photo.get("user", {})
            author = user.get("name")

            # Extract created date
            created_at = photo.get("created_at")
            published_at = None
            if created_at:
                try:
                    published_at = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00"),
                    )
                except ValueError:
                    pass

            # Extract description
            description = photo.get("description") or photo.get("alt_description")

            # Build domain tags from categories and tags
            domain_tags = []
            for tag in photo.get("tags", []):
                title = tag.get("title", "")
                if title:
                    domain_tags.append(title.lower())

            return NormalizedReferenceCard(
                provider="unsplash",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=description,
                author=author,
                license_id="Unsplash-License",
                attribution_text=self._build_attribution_text(
                    author=author,
                    provider="Unsplash",
                ),
                license_url="https://unsplash.com/license",
                domain_tags=domain_tags,
                published_at=published_at,
                collected_at=datetime.now(timezone.utc),
                raw_meta=photo,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Unsplash photo: {e}")
            return None
