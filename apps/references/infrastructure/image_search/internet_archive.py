"""Internet Archive Advanced Search adapter.

Internet Archive: https://archive.org/advancedsearch.php
License: Varies (PD/CC) - extracted per item
Tier: 2 (medium license risk - requires license metadata)
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter

logger = getLogger(__name__)


class InternetArchiveAdapter(ImageSearchAdapter):
    """Internet Archive Advanced Search adapter.

    API Documentation: https://archive.org/advancedsearch.php
    No API key required

    License filtering: Only returns results with license metadata
    Results without license metadata are DISCARDED.
    """

    BASE_URL = "https://archive.org/advancedsearch.php"
    TIER = 2

    def __init__(self):
        """Initialize Internet Archive adapter."""
        super().__init__(provider_id="internet_archive", tier=self.TIER)

    def is_available(self) -> bool:
        """Internet Archive is always available (no API key needed)."""
        return True

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search Internet Archive for images.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options

        Returns:
            List of normalized reference cards

        Note:
            DISCARDS results without license metadata.
        """
        # Build query with license filter
        # Only include items with license URL or public domain marker
        search_query = f'{query} AND (licenseurl:* OR publicdate:*) AND mediatype:(image)'

        # Build request parameters
        params = {
            "q": search_query,
            "fl[]": "identifier,title,creator,licenseurl,format,publicdate",
            "rows": min(count, 100),
            "output": "json",
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
            docs = data.get("response", {}).get("docs", [])

            for doc in docs:
                card = await self._normalize_archive_doc(doc)
                # DISCARD results without license metadata
                if card and card.license_id != "unknown":
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"Internet Archive API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Internet Archive search failed: {e}")
            raise

    async def _normalize_archive_doc(
        self,
        doc: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize Internet Archive document to standard card format.

        Args:
            doc: Internet Archive document

        Returns:
            Normalized reference card or None if invalid

        Note:
            Returns None if license metadata is missing.
        """
        try:
            # Extract basic info
            identifier = doc.get("identifier")
            title = doc.get("title")
            creator = doc.get("creator")

            if not identifier:
                return None

            # Extract license URL
            license_url = doc.get("licenseurl")
            if not license_url:
                logger.debug(f"Archive doc {identifier} missing license, discarding")
                return None

            # Map license URL to SPDX
            license_id = self._map_archive_license(license_url)

            # Build URLs
            external_url = f"https://archive.org/details/{identifier}"

            # Find first image file
            # This requires a metadata API call to get file list
            metadata_url = f"https://archive.org/metadata/{identifier}"

            try:
                meta_response = await self._client.get(metadata_url, timeout=5.0)
                meta_response.raise_for_status()
                metadata = meta_response.json()

                # Find first image file
                source_url = None
                for file_data in metadata.get("files", []):
                    format_ = file_data.get("format", "").lower()
                    if format_ in ("jpeg", "jpg", "png", "gif", "webp"):
                        source_url = f"https://archive.org/download/{identifier}/{file_data.get('name')}"
                        break

                if not source_url:
                    return None

                thumbnail_url = source_url  # IA doesn't provide separate thumbnails

                return NormalizedReferenceCard(
                    provider="internet_archive",
                    tier=self.TIER,
                    external_url=external_url,
                    source_url=source_url,
                    thumbnail_url=thumbnail_url,
                    title=title,
                    author=creator if isinstance(creator, str) else creator[0] if creator else None,
                    license_id=license_id,
                    attribution_text=self._build_attribution_text(
                        author=creator if isinstance(creator, str) else creator[0] if creator else None,
                        provider="Internet Archive",
                        license_name=license_id,
                    ),
                    license_url=license_url,
                    domain_tags=[],
                    published_at=None,
                    collected_at=datetime.now(timezone.utc),
                    raw_meta=doc,
                )

            except Exception as e:
                logger.warning(f"Failed to fetch IA metadata for {identifier}: {e}")
                return None

        except Exception as e:
            logger.warning(f"Failed to normalize Archive doc: {e}")
            return None

    def _map_archive_license(self, license_url: str) -> str:
        """Map Internet Archive license URL to SPDX identifier.

        Args:
            license_url: License URL from Archive

        Returns:
            SPDX license identifier or "unknown"
        """
        license_lower = license_url.lower()

        if "creativecommons.org/publicdomain/zero" in license_lower:
            return "CC0-1.0"
        elif "creativecommons.org/licenses/by" in license_lower:
            if "sa" in license_lower:
                return "CC-BY-SA-4.0"
            elif "nd" in license_lower:
                return "CC-BY-ND-4.0"
            elif "nc" in license_lower:
                return "CC-BY-NC-4.0"
            else:
                return "CC-BY-4.0"
        elif "publicdomain" in license_lower:
            return "PUBLIC-DOMAIN"
        else:
            return "unknown"
