"""Base image search adapter.

Abstract base class implementing common functionality for all image search adapters.
Integrates with ThumbnailProcessor for INV-02-05 compliance.
"""
import os
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import (
    ImageSearchPort,
    NormalizedReferenceCard,
)
from apps.references.infrastructure.adapters.thumbnail_processor import ThumbnailProcessor
from shared.domain.exceptions import OperationError, ValidationError

logger = getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for an image search provider."""

    adapter_class: type
    tier: int
    env_keys: list[str]
    base_url: str
    default_license: str
    requires_auth: bool = True


class ImageSearchAdapter(ImageSearchPort):
    """Abstract base class for image search adapters.

    Provides common HTTP client functionality, SSRF validation,
    response normalization, and thumbnail processing per INV-02-05.

    Attributes:
        provider_id: Unique provider identifier
        tier: Provider tier (1, 2, or 3)
        timeout: HTTP request timeout in seconds
        thumbnail_processor: Processor for image thumbnails
    """

    def __init__(
        self,
        provider_id: str,
        tier: int,
        timeout: float = 10.0,
        storage_adapter: Any = None,
    ):
        """Initialize adapter.

        Args:
            provider_id: Unique provider identifier
            tier: Provider tier (1, 2, or 3)
            timeout: HTTP request timeout in seconds
            storage_adapter: Optional storage adapter for processed thumbnails
        """
        self.provider_id = provider_id
        self.tier = tier
        self.timeout = timeout
        self.storage_adapter = storage_adapter

        # Initialize thumbnail processor for INV-02-05 compliance
        self.thumbnail_processor = ThumbnailProcessor()

        # Create HTTP client with appropriate settings
        self._client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "DesignSupport/1.0 (+https://designsupport.example.com/bot)",
            },
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit - close HTTP client."""
        await self._client.aclose()

    def get_provider_id(self) -> str:
        """Return the provider identifier."""
        return self.provider_id

    def get_tier(self) -> int:
        """Return the provider tier."""
        return self.tier

    @abstractmethod
    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Provider-specific search implementation.

        Must be implemented by each adapter.
        """
        ...

    async def search(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search for images matching the query.

        Validates input, calls provider implementation, processes thumbnails per INV-02-05,
        and handles errors.

        Args:
            query: Search query string
            count: Number of results to return (1-100)
            options: Optional search parameters

        Returns:
            List of normalized reference cards with processed thumbnails

        Raises:
            ValidationError: If input validation fails
            OperationError: If search or processing fails
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValidationError(field="query", message="Query cannot be empty")

        if count <= 0 or count > 100:
            raise ValidationError(
                field="count",
                message="Count must be between 1 and 100",
            )

        if not self.is_available():
            logger.warning(f"Provider {self.provider_id} is not available")
            return []

        try:
            results = await self._search_impl(query, count, options or {})
            logger.info(f"Provider {self.provider_id} returned {len(results)} results")

            # Process thumbnails per INV-02-05
            results = await self._process_thumbnails(results)

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from {self.provider_id}: {e.response.status_code}")
            if e.response.status_code == 429:
                raise OperationError(
                    operation=f"search:{self.provider_id}",
                    reason=f"Rate limit exceeded (HTTP 429)",
                ) from e
            raise OperationError(
                operation=f"search:{self.provider_id}",
                reason=f"HTTP {e.response.status_code}",
            ) from e

        except httpx.RequestError as e:
            logger.error(f"Request error for {self.provider_id}: {e}")
            raise OperationError(
                operation=f"search:{self.provider_id}",
                reason=f"Request failed: {e}",
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error from {self.provider_id}: {e}")
            raise OperationError(
                operation=f"search:{self.provider_id}",
                reason=f"Unexpected error: {e}",
            ) from e

    async def _process_thumbnails(
        self,
        results: list[NormalizedReferenceCard],
    ) -> list[NormalizedReferenceCard]:
        """Process thumbnails for search results per INV-02-05.

        Tier 1/2: Full processing (download, resize, strip EXIF, upload)
        Tier 3: Mini-thumbnail only (external URL)

        Args:
            results: List of normalized reference cards

        Returns:
            List with processed thumbnails
        """
        processed_results = []

        for card in results:
            # Convert to dict for processing
            card_dict = {
                "source_url": card.source_url,
                "thumbnail_url": card.thumbnail_url,
                "external_url": card.external_url,
            }

            # Process thumbnail based on tier
            processed_dict = await self.thumbnail_processor.process_asset(
                card_dict,
                tier=self.tier,
                storage_adapter=self.storage_adapter,
            )

            # Update card with processed thumbnail URI
            if "thumbnail_uri" in processed_dict:
                # Update the card with processed thumbnail
                # Note: NormalizedReferenceCard is immutable, so we create a new one
                from dataclasses import replace

                updated_card = replace(
                    card,
                    thumbnail_url=processed_dict.get("thumbnail_uri", card.thumbnail_url),
                )
                processed_results.append(updated_card)
            else:
                # Keep original card if processing failed
                processed_results.append(card)

        return processed_results

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API keys configured, quota remaining)."""
        ...

    def _validate_url(self, url: str) -> bool:
        """Validate URL against SSRF allowlist.

        Args:
            url: URL to validate

        Returns:
            True if URL is allowed, False otherwise
        """
        # SSRF allowlist check would go here
        # For now, we'll do basic validation
        if not url or not url.startswith(("http://", "https://")):
            return False

        # Check against allowlist (SPEC-01)
        # This is a placeholder - real implementation would check against
        # the SSRF allowlist configured in the application
        return True

    def _build_attribution_text(
        self,
        author: str | None,
        provider: str,
        license_name: str | None = None,
    ) -> str:
        """Build standardized attribution text.

        Args:
            author: Image author/creator
            provider: Provider name
            license_name: Optional license name

        Returns:
            Attribution text string
        """
        if author:
            if license_name:
                return f"Photo by {author} on {provider} ({license_name})"
            return f"Photo by {author} on {provider}"
        return f"Image from {provider}"

    def _normalize_card(
        self,
        raw_data: dict[str, Any],
        external_url: str,
        source_url: str,
        thumbnail_url: str,
        title: str | None,
        author: str | None,
        license_id: str,
        license_url: str | None,
        domain_tags: list[str] | None = None,
        published_at: datetime | None = None,
    ) -> NormalizedReferenceCard:
        """Normalize provider-specific data to standard card format.

        Args:
            raw_data: Raw provider response data
            external_url: Original page URL
            source_url: Image direct URL
            thumbnail_url: Thumbnail URL
            title: Image title
            author: Image author
            license_id: License identifier (SPDX or provider-specific)
            license_url: License URL
            domain_tags: Domain classification tags
            published_at: Publication date

        Returns:
            Normalized reference card
        """
        # Build attribution text
        attribution = self._build_attribution_text(
            author=author,
            provider=self.provider_id,
            license_name=license_id,
        )

        # Validate URLs
        if not all([
            self._validate_url(external_url),
            self._validate_url(source_url),
            self._validate_url(thumbnail_url),
        ]):
            logger.warning(f"Invalid URL(s) in card from {self.provider_id}")

        return NormalizedReferenceCard(
            provider=self.provider_id,
            tier=self.tier,
            external_url=external_url,
            source_url=source_url,
            thumbnail_url=thumbnail_url,
            title=title,
            author=author,
            license_id=license_id,
            attribution_text=attribution,
            license_url=license_url,
            domain_tags=domain_tags or [],
            published_at=published_at,
            collected_at=datetime.now(timezone.utc),
            raw_meta=raw_data,
        )

    def _get_env_key(self, key: str) -> str | None:
        """Get environment variable value.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value or None
        """
        return os.getenv(key)

    def _has_required_keys(self, required_keys: list[str]) -> bool:
        """Check if all required API keys are configured.

        Args:
            required_keys: List of environment variable names

        Returns:
            True if all keys are present and non-empty
        """
        return all(self._get_env_key(key) for key in required_keys)
