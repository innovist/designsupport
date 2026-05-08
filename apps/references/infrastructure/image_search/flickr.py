"""Flickr image search adapter with CC license filter.

Flickr API: https://www.flickr.com/services/api/
License: Varies (CC licenses only - filtered)
Tier: 2 (medium license risk - requires license metadata)
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter
from shared.domain.exceptions import ValidationError

logger = getLogger(__name__)


class FlickrAdapter(ImageSearchAdapter):
    """Flickr image search adapter with CC license filtering.

    API Documentation: https://www.flickr.com/services/api/flickr.photos.search.html
    Requires: FLICKR_API_KEY environment variable

    License filtering: Only returns results with CC licenses (1, 2, 3, 4, 5, 6, 9, 10)
    Results without license metadata are DISCARDED.
    """

    BASE_URL = "https://www.flickr.com/services/rest"
    TIER = 2

    # Flickr CC license IDs (only these are allowed)
    CC_LICENSES = "1,2,3,4,5,6,9,10"

    def __init__(self):
        """Initialize Flickr adapter."""
        api_key = self._get_env_key("FLICKR_API_KEY")
        if not api_key:
            logger.warning("FLICKR_API_KEY not configured")

        super().__init__(provider_id="flickr", tier=self.TIER)

        self._api_key = api_key

    def is_available(self) -> bool:
        """Check if Flickr API key is configured."""
        return bool(self._get_env_key("FLICKR_API_KEY"))

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Flickr for CC-licensed photos.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options

        Returns:
            List of normalized reference cards

        Note:
            DISCARDS results without license metadata.
            Only returns CC-licensed photos.
        """
        if not self.is_available():
            raise ValidationError("Flickr API key not configured")

        # Build request parameters
        params = {
            "method": "flickr.photos.search",
            "api_key": self._api_key,
            "text": query,
            "license": self.CC_LICENSES,  # CC licenses only
            "per_page": min(count, 500),
            "extras": "license,owner_name,url_o,url_m,description",
            "format": "json",
            "nojsoncallback": "1",
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
            photos = data.get("photos", {}).get("photo", [])

            for photo in photos:
                card = self._normalize_flickr_photo(photo)
                # DISCARD results without license metadata
                if card and card.license_id != "unknown":
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Flickr API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Flickr search failed: {e}")
            raise

    def _normalize_flickr_photo(
        self,
        photo: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Flickr photo data to standard card format.

        Args:
            photo: Flickr photo object

        Returns:
            Normalized reference card or None if invalid

        Note:
            Returns None if license metadata is missing.
        """
        try:
            # Extract license ID
            license_id = photo.get("license")
            if not license_id or license_id == "0":
                # No license or All Rights Reserved
                logger.debug("Flickr photo missing CC license, discarding")
                return None

            # Map Flickr license ID to SPDX
            spdx_license = self._map_flickr_license(license_id)

            # Extract photo ID
            photo_id = photo.get("id")
            owner = photo.get("owner")
            if not all([photo_id, owner]):
                return None

            # Build URLs
            farm = photo.get("farm")
            server = photo.get("server")
            secret = photo.get("secret")

            # Build source URL (prefer original, fallback medium)
            source_url = photo.get("url_o")
            if not source_url:
                source_url = f"https://live.staticflickr.com/{server}/{photo_id}_{secret}.jpg"

            # Build thumbnail URL
            thumbnail_url = photo.get("url_m") or source_url

            # Build external URL
            external_url = f"https://www.flickr.com/photos/{owner}/{photo_id}"

            # Extract title/description
            title = photo.get("title")
            description = photo.get("description", {}).get("_content")

            # Extract author
            author = photo.get("ownername")

            return NormalizedReferenceCard(
                provider="flickr",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title or description,
                author=author,
                license_id=spdx_license,
                attribution_text=self._build_attribution_text(
                    author=author,
                    provider="Flickr",
                    license_name=spdx_license,
                ),
                license_url=self._get_license_url(spdx_license),
                domain_tags=[],
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta=photo,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Flickr photo: {e}")
            return None

    def _map_flickr_license(self, flickr_license: str) -> str:
        """Map Flickr license ID to SPDX identifier.

        Args:
            flickr_license: Flickr license ID

        Returns:
            SPDX license identifier or "unknown"
        """
        license_map = {
            "1": "CC-BY-4.0",  # CC BY
            "2": "CC-BY-SA-4.0",  # CC BY-SA
            "3": "CC-BY-ND-4.0",  # CC BY-ND
            "4": "CC-BY-NC-4.0",  # CC BY-NC
            "5": "CC-BY-NC-SA-4.0",  # CC BY-NC-SA
            "6": "CC-BY-NC-ND-4.0",  # CC BY-NC-ND
            "9": "CC0-1.0",  # CC0
            "10": "PUBLIC-DOMAIN",  # Public Domain Mark
        }

        return license_map.get(flickr_license, "unknown")

    def _get_license_url(self, spdx_license: str) -> str | None:
        """Get license URL for SPDX identifier.

        Args:
            spdx_license: SPDX license identifier

        Returns:
            License URL or None
        """
        license_urls = {
            "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
            "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
            "CC-BY-ND-4.0": "https://creativecommons.org/licenses/by-nd/4.0/",
            "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
            "CC-BY-NC-SA-4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
            "CC-BY-NC-ND-4.0": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
            "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
            "PUBLIC-DOMAIN": "https://creativecommons.org/publicdomain/mark/1.0/",
        }

        return license_urls.get(spdx_license)
