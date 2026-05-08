"""Europeana image search adapter.

Europeana API: https://api.europeana.eu/record/v2/search.json
License: Varies (per-item) - extracted from response
Tier: 1
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter

logger = getLogger(__name__)


class EuropeanaAdapter(ImageSearchAdapter):
    """Europeana image search adapter.

    API Documentation: https://pro.europeana.eu/resources/apis/search/
    Requires EUROPEANA_API_KEY environment variable
    """

    BASE_URL = "https://api.europeana.eu/record/v2"
    TIER = 1

    def __init__(self):
        """Initialize Europeana adapter."""
        super().__init__(provider_id="europeana", tier=self.TIER)
        self.api_key = self._get_env_key("EUROPEANA_API_KEY")

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Europeana for cultural heritage images.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (filters, etc.)

        Returns:
            List of normalized reference cards
        """
        if not self.api_key:
            logger.warning("Europeana API key not configured")
            return []

        # Build request parameters
        params = {
            "wskey": self.api_key,
            "query": f'("{query}") AND TYPE:IMAGE',
            "rows": min(count, 100),
            "profile": "minimal",
        }

        # Add optional filters
        if options:
            if "reusability" in options:
                params["reusability"] = options["reusability"]
            if "qf" in options:
                params["qf"] = options["qf"]

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search.json",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "error" in data:
                logger.error(f"Europeana API error: {data['error']}")
                return []

            # Normalize results
            results = []
            items = data.get("items", [])

            for item in items:
                card = self._normalize_europeana_result(item)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Europeana API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Europeana search failed: {e}")
            raise

    def _normalize_europeana_result(
        self,
        item: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Europeana result data to standard card format.

        Args:
            item: Europeana result object

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            title = self._extract_title(item)
            external_url = item.get("link", "")

            # Extract image URLs
            # Europeana provides edmIsShownBy (high-res) and edmPreview (thumbnail)
            source_url = ""
            thumbnail_url = ""

            aggregations = item.get("aggregations", [])
            if aggregations and isinstance(aggregations, list):
                agg = aggregations[0]
                # edmIsShownBy is the high-res image
                source_url = agg.get("edmIsShownBy", "")
                # edmPreview is the thumbnail
                thumbnail_url = agg.get("edmPreview", [source_url])[0] if agg.get("edmPreview") else source_url

            # Fallback to link if no image URL
            if not source_url:
                source_url = external_url
            if not thumbnail_url:
                thumbnail_url = source_url

            if not all([external_url, source_url]):
                logger.warning("Europeana result missing required URLs")
                return None

            # Extract provider/dataProvider
            provider_name = item.get("dataProvider", [None])[0] if item.get("dataProvider") else None
            if not provider_name:
                provider_name = item.get("provider", [None])[0] if item.get("provider") else "Europeana"

            # Extract license information
            rights = item.get("rights", [None])[0] if item.get("rights") else None
            license_id = self._map_license(rights)
            license_url = rights

            # Build attribution
            attribution = self._build_attribution_text(
                author=None,  # Europeana typically doesn't provide individual authors
                provider=provider_name or "Europeana",
                license_name=license_id,
            )

            # Extract domain tags from concepts (if available)
            domain_tags = []
            concepts = item.get("concepts", [])
            if concepts:
                for concept in concepts[:3]:  # Limit to first 3 concepts
                    if isinstance(concept, dict):
                        pref_label = concept.get("prefLabel", {})
                        if isinstance(pref_label, dict) and "en" in pref_label:
                            domain_tags.append(pref_label["en"].lower())

            return NormalizedReferenceCard(
                provider="europeana",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=None,  # Europeana items are typically institutional, not individual authors
                license_id=license_id,
                attribution_text=attribution,
                license_url=license_url,
                domain_tags=domain_tags,
                published_at=None,  # Europeana doesn't always provide consistent dates
                collected_at=datetime.now(timezone.utc),
                raw_meta=item,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize Europeana result: {e}")
            return None

    def _extract_title(self, item: dict[str, Any]) -> str | None:
        """Extract title from Europeana item.

        Args:
            item: Europeana result object

        Returns:
            Title string or None
        """
        # Try dcTitle first
        title_data = item.get("dcTitle", {})
        if isinstance(title_data, dict) and "en" in title_data:
            return title_data["en"]

        # Fallback to title list
        if isinstance(title_data, list) and title_data:
            return str(title_data[0])

        return None

    def _map_license(self, rights: str | None) -> str:
        """Map Europeana rights to SPDX license identifiers.

        Args:
            rights: Europeana rights string

        Returns:
            SPDX license identifier
        """
        if not rights:
            return "unknown"

        rights_lower = rights.lower()

        # Map common Europeana rights to SPDX
        if "creativecommons.org/publicdomain/zero/1.0" in rights_lower:
            return "CC0-1.0"
        elif "creativecommons.org/licenses/by/4.0" in rights_lower:
            return "CC-BY-4.0"
        elif "creativecommons.org/licenses/by-sa/4.0" in rights_lower:
            return "CC-BY-SA-4.0"
        elif "creativecommons.org/licenses/by-nc/4.0" in rights_lower:
            return "CC-BY-NC-4.0"
        elif "creativecommons.org/licenses/by-nc-sa/4.0" in rights_lower:
            return "CC-BY-NC-SA-4.0"
        elif "publicdomain" in rights_lower:
            return "public-domain"
        elif "copyright" in rights_lower or "all rights reserved" in rights_lower:
            return "all-rights-reserved"
        else:
            return "unknown"
