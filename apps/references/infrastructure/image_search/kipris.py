"""KIPRIS (Korean Intellectual Property Rights Information Service) design search adapter.

KIPRIS API: http://plus.kipris.or.kr/openapi/rest/design
License: Government open data (Korean design registration)
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


class KiprisAdapter(ImageSearchAdapter):
    """KIPRIS design search adapter.

    API Documentation: http://plus.kipris.or.kr/openapi/rest/OpenApiInfo.do
    Requires: KIPRIS_API_KEY environment variable
    """

    BASE_URL = "http://plus.kipris.or.kr/openapi/rest/design"
    TIER = 1

    def __init__(self):
        """Initialize KIPRIS adapter."""
        api_key = self._get_env_key("KIPRIS_API_KEY")
        if not api_key:
            logger.warning("KIPRIS_API_KEY not configured")

        super().__init__(provider_id="kipris", tier=self.TIER)

        self._api_key = api_key

    def is_available(self) -> bool:
        """Check if KIPRIS API key is configured."""
        return bool(self._get_env_key("KIPRIS_API_KEY"))

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search KIPRIS for design registrations.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options

        Returns:
            List of normalized reference cards
        """
        if not self.is_available():
            raise ValidationError("KIPRIS API key not configured")

        # Build request parameters for design search
        params = {
            "accessKey": self._api_key,
            "searchString": query,
            "numOfRows": min(count, 100),
        }

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/searchAdvanced",
                params=params,
            )
            response.raise_for_status()

            # KIPRIS returns XML, parse it
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)

            # Normalize results
            results = []
            for item in root.findall(".//item"):
                card = self._normalize_kipris_item(item)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"KIPRIS API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"KIPRIS search failed: {e}")
            raise

    def _normalize_kipris_item(
        self,
        item: Any,
    ) -> NormalizedReferenceCard | None:
        """Normalize KIPRIS item data to standard card format.

        Args:
            item: KIPRIS item XML element

        Returns:
            Normalized reference card or None if invalid
        """
        try:
            # Extract basic info
            app_number = self._get_xml_text(item, "applicationNumber")
            title = self._get_xml_text(item, "designTitle")

            # KIPRIS may not provide direct image URLs in search results
            # Build external URL to the detail page
            external_url = f"http://plus.kipris.or.kr/ipo/CC02002?appNumber={app_number}"

            # Placeholder URLs (real implementation would fetch detail page)
            source_url = external_url
            thumbnail_url = external_url

            # Extract applicant/author
            applicant = self._get_xml_text(item, "applicantName")

            return NormalizedReferenceCard(
                provider="kipris",
                tier=self.TIER,
                external_url=external_url,
                source_url=source_url,
                thumbnail_url=thumbnail_url,
                title=title,
                author=applicant,
                license_id="KR-Government-Open",
                attribution_text=f"Design Registration {app_number}, KIPRIS",
                license_url="http://plus.kipris.or.kr/openapi/rest/OpenApiInfo.do",
                domain_tags=["industrial", "design"],
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta={"xml": str(item)},
            )

        except Exception as e:
            logger.warning(f"Failed to normalize KIPRIS item: {e}")
            return None

    def _get_xml_text(self, element: Any, tag: str) -> str | None:
        """Extract text from XML element.

        Args:
            element: XML element
            tag: Tag name to extract

        Returns:
            Text content or None
        """
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
