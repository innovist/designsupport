"""Web search image adapter (SerpAPI/Bing/DuckDuckGo).

Web Search: SerpAPI, Bing Image Search, or DuckDuckGo
License: Varies (CC filtered)
Tier: 2 for results with license, Tier 3 for those without
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter
from shared.domain.exceptions import ValidationError

logger = getLogger(__name__)


class WebSearchAdapter(ImageSearchAdapter):
    """Web search image adapter with usage_rights filtering.

    Supports:
    - SerpAPI (Google Images)
    - Bing Image Search
    - DuckDuckGo

    MUST enforce usage_rights=cc_* filter parameter.

    Results with license metadata: tier=2
    Results without license metadata: tier=3
    """

    TIER = 2  # Default tier (will be adjusted per result)

    def __init__(self):
        """Initialize web search adapter."""
        super().__init__(provider_id="web_search", tier=self.TIER)

        # Detect which API is available
        self._api_type = None
        self._api_key = None

        if self._get_env_key("SERPAPI_KEY"):
            self._api_type = "serpapi"
            self._api_key = self._get_env_key("SERPAPI_KEY")
        elif self._get_env_key("BING_SEARCH_KEY"):
            self._api_type = "bing"
            self._api_key = self._get_env_key("BING_SEARCH_KEY")
        else:
            logger.warning("No web search API key configured (SERPAPI_KEY or BING_SEARCH_KEY)")

    def is_available(self) -> bool:
        """Check if any web search API key is configured."""
        return bool(self._api_type)

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search web for images with usage rights filter.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options

        Returns:
            List of normalized reference cards

        Note:
            MUST enforce usage_rights=cc_* filter.
            Results with license: tier=2
            Results without license: tier=3
        """
        if not self.is_available():
            raise ValidationError("Web search API key not configured")

        if self._api_type == "serpapi":
            return await self._search_serpapi(query, count, options)
        elif self._api_type == "bing":
            return await self._search_bing(query, count, options)
        else:
            logger.warning("No web search API available")
            return []

    async def _search_serpapi(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search using SerpAPI (Google Images).

        Args:
            query: Search query
            count: Number of results
            options: Additional options

        Returns:
            List of normalized reference cards
        """
        # Build request parameters with MANDATORY usage rights filter
        params = {
            "engine": "google_images",
            "q": query,
            "num": min(count, 100),
            "filter": "1",  # Safe search
            "api_key": self._api_key,
        }

        # MANDATORY: Add usage rights filter for CC licenses
        # This enforces NFR-02-COMP-002
        params["tbs"] = "il:cl"  # Commercial reuse with modification

        try:
            response = await self._client.get(
                "https://serpapi.com/search.json",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            images_info = data.get("images_info", [])

            for img in images_info:
                card = self._normalize_serpapi_image(img)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"SerpAPI error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            raise

    async def _search_bing(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search using Bing Image Search.

        Args:
            query: Search query
            count: Number of results
            options: Additional options

        Returns:
            List of normalized reference cards
        """
        # Build request parameters with MANDATORY license filter
        params = {
            "q": query,
            "count": min(count, 150),
            "license": "AllPublic",  # MANDATORY: CC/PD only
            "imageType": "Photo",
        }

        headers = {
            "Ocp-Apim-Subscription-Key": self._api_key,
        }

        try:
            response = await self._client.get(
                "https://api.bing.microsoft.com/v7.0/images/search",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            values = data.get("value", [])

            for img in values:
                card = self._normalize_bing_image(img)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Bing API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            raise

    def _normalize_serpapi_image(
        self,
        img: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize SerpAPI image data to standard card format.

        Args:
            img: SerpAPI image object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract URLs
            source_url = img.get("original")
            thumbnail_url = img.get("thumbnail")
            external_url = img.get("link") or source_url

            if not all([source_url, thumbnail_url]):
                return None

            # Extract title
            title = img.get("title")

            # SerpAPI doesn't provide license metadata
            # Default to tier=3 (unknown license)
            return NormalizedReferenceCard(
                provider="web_search",
                tier=3,  # Unknown license
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=None,
                license_id="unknown",
                attribution_text="Image from web search (license unknown)",
                license_url=None,
                domain_tags=[],
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta=img,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize SerpAPI image: {e}")
            return None

    def _normalize_bing_image(
        self,
        img: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Bing image data to standard card format.

        Args:
            img: Bing image object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract URLs
            source_url = img.get("contentUrl")
            thumbnail_url = img.get("thumbnailUrl")
            external_url = img.get("hostPageUrl") or source_url

            if not all([source_url, thumbnail_url]):
                return None

            # Extract title
            title = img.get("name")

            # Check license metadata
            license_data = img.get("license", {})
            license_id = license_data.get("licenseUrl", "unknown")

            # Determine tier based on license
            if license_id == "unknown":
                tier = 3
            else:
                tier = 2

            return NormalizedReferenceCard(
                provider="web_search",
                tier=tier,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=None,
                license_id=license_id,
                attribution_text=self._build_attribution_text(
                    author=None,
                    provider="Web Search",
                ),
                license_url=license_data.get("licenseUrl") if license_id != "unknown" else None,
                domain_tags=[],
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta=img,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Bing image: {e}")
            return None
