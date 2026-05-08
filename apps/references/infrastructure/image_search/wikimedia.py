"""Wikimedia Commons image search adapter.

Wikimedia Commons API: https://commons.wikimedia.org/w/api.php
License: Varies (CC0, CC-BY, CC-BY-SA, Public Domain) - extracted per item
Tier: 1
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any
from urllib.parse import quote

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter

logger = getLogger(__name__)


class WikimediaAdapter(ImageSearchAdapter):
    """Wikimedia Commons image search adapter.

    API Documentation: https://www.mediawiki.org/wiki/API:Search
    No API key required (User-Agent identification required)
    """

    BASE_URL = "https://commons.wikimedia.org/w/api.php"
    TIER = 1

    def __init__(self):
        """Initialize Wikimedia adapter."""
        super().__init__(provider_id="wikimedia", tier=self.TIER)

    def is_available(self) -> bool:
        """Wikimedia Commons is always available (no API key needed)."""
        return True

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Wikimedia Commons for images.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (namespace, limit, etc.)

        Returns:
            List of normalized reference cards
        """
        # Build request parameters for image search
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": "6",  # File namespace
            "gsrlimit": min(count, 50),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "1024",
            "format": "json",
        }

        try:
            response = await self._client.get(
                self.BASE_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            query_pages = data.get("query", {}).get("pages", {})

            for page_id, page_data in query_pages.items():
                if page_id == -1:  # Invalid page
                    continue

                card = await self._normalize_wikimedia_page(page_data)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Wikimedia API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Wikimedia search failed: {e}")
            raise

    async def _normalize_wikimedia_page(
        self,
        page_data: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Wikimedia page data to standard card format.

        Args:
            page_data: Wikimedia page object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract title and page URL
            title = page_data.get("title", "")
            if not title:
                return None

            # Build page URL
            encoded_title = quote(title.replace(" ", "_"), safe="/:")
            external_url = f"https://commons.wikimedia.org/wiki/{encoded_title}"

            # Extract image info
            imageinfo = page_data.get("imageinfo", [])
            if not imageinfo:
                return None

            info = imageinfo[0]
            source_url = info.get("url", "")
            thumb_url = info.get("thumburl", "")

            if not all([external_url, source_url, thumb_url]):
                return None

            # Extract metadata
            extmetadata = info.get("extmetadata", {})

            # Extract license information
            license_short_name = extmetadata.get("LicenseShortName", {}).get("value", "Unknown")
            license_url = extmetadata.get("LicenseUrl", {}).get("value")

            # Map common licenses to SPDX
            license_id = self._map_wikimedia_license(license_short_name)

            # Extract artist/author
            artist = extmetadata.get("Artist", {}).get("value", "")
            # Clean up HTML tags from artist field
            import re
            author = re.sub(r'<[^>]+>', '', artist).strip() or None

            # Extract description
            description = extmetadata.get("ImageDescription", {}).get("value", "")
            # Clean up HTML tags
            desc_clean = re.sub(r'<[^>]+>', '', description).strip() or None

            return NormalizedReferenceCard(
                provider="wikimedia",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumb_url,
                title=desc_clean or title,
                author=author,
                license_id=license_id,
                attribution_text=self._build_attribution_text(
                    author=author,
                    provider="Wikimedia Commons",
                    license_name=license_short_name,
                ),
                license_url=license_url,
                domain_tags=[],  # Wikimedia doesn't provide domain tags
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta=page_data,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Wikimedia page: {e}")
            return None

    def _map_wikimedia_license(self, license_name: str) -> str:
        """Map Wikimedia license name to SPDX identifier.

        Args:
            license_name: Wikimedia license name

        Returns:
            SPDX license identifier or "unknown"
        """
        license_lower = license_name.lower()

        if "public domain" in license_lower or "pd" in license_lower:
            return "PUBLIC-DOMAIN"
        elif "cc0" in license_lower:
            return "CC0-1.0"
        elif "cc-by-sa" in license_lower:
            return "CC-BY-SA-4.0"
        elif "cc-by" in license_lower:
            return "CC-BY-4.0"
        elif "cc-sa" in license_lower:
            return "CC-SA-4.0"
        else:
            return "unknown"
