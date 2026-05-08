"""References application ports.

Abstract interfaces for infrastructure adapters.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class NormalizedReferenceCard:
    """Normalized response card from all image search adapters.

    All adapters must return this format for consistent handling in application layer.
    """
    provider: str
    tier: int  # 1, 2, or 3
    external_url: str  # Original page URL (for attribution)
    source_url: str  # Image direct URL
    thumbnail_url: str  # Provider thumbnail URL
    title: str | None
    author: str | None
    license_id: str  # SPDX or "unknown"
    attribution_text: str
    license_url: str | None
    domain_tags: list[str]
    published_at: datetime | None
    collected_at: datetime
    raw_meta: dict[str, Any]  # Provider-specific raw metadata


class ImageSearchPort(ABC):
    """Abstract interface for image search adapters.

    All provider adapters must implement this port.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search for images matching the query.

        Args:
            query: Search query string
            count: Maximum number of results to return
            options: Additional search options (filters, sort, etc.)

        Returns:
            List of normalized reference cards

        Raises:
            ValidationError: If query parameters are invalid
            OperationError: If search operation fails
        """
        ...

    @abstractmethod
    def get_provider_id(self) -> str:
        """Return the provider identifier."""
        ...

    @abstractmethod
    def get_tier(self) -> int:
        """Return the provider tier (1, 2, or 3)."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API keys configured, quota remaining)."""
        ...


class ReferenceAssetRepositoryPort(ABC):
    """Abstract interface for reference asset repository."""

    @abstractmethod
    async def save(self, asset: Any) -> Any:
        """Save reference asset to database."""
        ...

    @abstractmethod
    async def find_by_id(self, asset_id: UUID) -> Any | None:
        """Find reference asset by ID."""
        ...

    @abstractmethod
    async def find_by_session(
        self,
        session_id: UUID,
        limit: int = 100,
    ) -> list[Any]:
        """Find all assets for a session."""
        ...

    @abstractmethod
    async def delete(self, asset_id: UUID) -> bool:
        """Delete reference asset by ID."""
        ...


class ReferenceAnalysisRepositoryPort(ABC):
    """Abstract interface for reference analysis repository."""

    @abstractmethod
    async def save(self, analysis: Any) -> Any:
        """Save reference analysis to database."""
        ...

    @abstractmethod
    async def find_by_asset_id(self, asset_id: UUID) -> Any | None:
        """Find analysis by asset ID."""
        ...

    @abstractmethod
    async def find_by_id(self, analysis_id: UUID) -> Any | None:
        """Find analysis by ID."""
        ...


class QuotaRepositoryPort(ABC):
    """Abstract interface for quota management repository."""

    @abstractmethod
    async def get_quota(self, provider: str) -> Any | None:
        """Get quota record for provider."""
        ...

    @abstractmethod
    async def save_quota(self, quota: Any) -> Any:
        """Save or update quota record."""
        ...

    @abstractmethod
    async def check_and_increment(self, provider: str) -> bool:
        """Check if provider can make a call and increment usage.

        Returns True if call allowed, False if quota exceeded.
        """
        ...

    @abstractmethod
    async def reset_daily_counters(self) -> None:
        """Reset daily counters for providers that need reset."""
        ...


class ThumbnailPort(ABC):
    """Abstract interface for thumbnail processing."""

    @abstractmethod
    async def process_url(
        self,
        image_url: str,
        max_edge_px: int = 1024,
    ) -> str:
        """Download and process image to thumbnail.

        Args:
            image_url: URL of source image
            max_edge_px: Maximum edge length in pixels

        Returns:
            Storage URI of processed thumbnail
        """
        ...

    @abstractmethod
    async def process_file(
        self,
        image_path: str,
        output_path: str,
        max_edge_px: int = 1024,
    ) -> bool:
        """Process local image file to thumbnail.

        Args:
            image_path: Path to source image
            output_path: Path for processed output
            max_edge_px: Maximum edge length in pixels

        Returns:
            True if successful, False otherwise
        """
        ...


class ModelPort(ABC):
    """Port for model catalog operations."""

    @abstractmethod
    async def get_active_model(self, provider: str | None = None) -> dict | None:
        """Get active model for generation.

        Args:
            provider: Optional provider filter

        Returns:
            Model configuration dictionary if found, None otherwise
        """
        ...

    @abstractmethod
    async def list_models(self, provider: str | None = None) -> list[dict]:
        """List available models.

        Args:
            provider: Optional provider filter

        Returns:
            List of model configuration dictionaries
        """
        ...
