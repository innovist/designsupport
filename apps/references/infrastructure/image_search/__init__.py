"""Image search adapter registry.

Data-driven registry pattern for managing image search providers.
NO if/elif provider branching - use registry for all provider access.
"""
import os
from logging import getLogger

from apps.references.application.ports import ImageSearchPort
from apps.references.infrastructure.image_search.base import (
    ImageSearchAdapter,
    ProviderConfig,
)

# Import all adapters
from apps.references.infrastructure.image_search.europeana import EuropeanaAdapter
from apps.references.infrastructure.image_search.flickr import FlickrAdapter
from apps.references.infrastructure.image_search.internet_archive import InternetArchiveAdapter
from apps.references.infrastructure.image_search.kipris import KiprisAdapter
from apps.references.infrastructure.image_search.met import MetAdapter
from apps.references.infrastructure.image_search.nasa import NasaAdapter
from apps.references.infrastructure.image_search.openverse import OpenverseAdapter
from apps.references.infrastructure.image_search.pexels import PexelsAdapter
from apps.references.infrastructure.image_search.pixabay import PixabayAdapter
from apps.references.infrastructure.image_search.rijks import RijksAdapter
from apps.references.infrastructure.image_search.smithsonian import SmithsonianAdapter
from apps.references.infrastructure.image_search.unsplash import UnsplashAdapter
from apps.references.infrastructure.image_search.web_search import WebSearchAdapter
from apps.references.infrastructure.image_search.wikimedia import WikimediaAdapter
from apps.references.infrastructure.image_search.youtube_thumbnail import YouTubeThumbnailAdapter

logger = getLogger(__name__)

# Provider registry - data-driven configuration
# NO CODE SHOULD USE IF/ELIF ON PROVIDER NAMES - USE THIS REGISTRY
PROVIDER_REGISTRY: dict[str, ProviderConfig] = {
    # Tier 1 - Direct use providers
    "unsplash": ProviderConfig(
        adapter_class=UnsplashAdapter,
        tier=1,
        env_keys=["UNSPLASH_ACCESS_KEY"],
        base_url="https://api.unsplash.com",
        default_license="Unsplash-License",
        requires_auth=True,
    ),
    "pexels": ProviderConfig(
        adapter_class=PexelsAdapter,
        tier=1,
        env_keys=["PEXELS_API_KEY"],
        base_url="https://api.pexels.com/v1",
        default_license="Pexels-License",
        requires_auth=True,
    ),
    "pixabay": ProviderConfig(
        adapter_class=PixabayAdapter,
        tier=1,
        env_keys=["PIXABAY_API_KEY"],
        base_url="https://pixabay.com/api",
        default_license="Pixabay-Content-License",
        requires_auth=True,
    ),
    "wikimedia": ProviderConfig(
        adapter_class=WikimediaAdapter,
        tier=1,
        env_keys=[],
        base_url="https://commons.wikimedia.org/w/api.php",
        default_license="(per-item)",
        requires_auth=False,
    ),
    "openverse": ProviderConfig(
        adapter_class=OpenverseAdapter,
        tier=1,
        env_keys=[],
        base_url="https://api.openverse.org/v1",
        default_license="(per-item CC)",
        requires_auth=False,
    ),
    "met": ProviderConfig(
        adapter_class=MetAdapter,
        tier=1,
        env_keys=[],
        base_url="https://collectionapi.metmuseum.org/public/collection/v1",
        default_license="CC0-1.0",
        requires_auth=False,
    ),
    "smithsonian": ProviderConfig(
        adapter_class=SmithsonianAdapter,
        tier=1,
        env_keys=["SMITHSONIAN_API_KEY"],
        base_url="https://api.si.edu/openaccess/api/v1.0",
        default_license="CC0-1.0",
        requires_auth=True,
    ),
    "europeana": ProviderConfig(
        adapter_class=EuropeanaAdapter,
        tier=1,
        env_keys=["EUROPEANA_API_KEY"],
        base_url="https://api.europeana.eu/record/v2",
        default_license="(per-item)",
        requires_auth=True,
    ),
    "rijks": ProviderConfig(
        adapter_class=RijksAdapter,
        tier=1,
        env_keys=["RIJKS_API_KEY"],
        base_url="https://www.rijksmuseum.nl/api/en/collection",
        default_license="CC0-1.0",
        requires_auth=True,
    ),
    "nasa": ProviderConfig(
        adapter_class=NasaAdapter,
        tier=1,
        env_keys=[],
        base_url="https://images-api.nasa.gov",
        default_license="Public-Domain",
        requires_auth=False,
    ),
    "kipris": ProviderConfig(
        adapter_class=KiprisAdapter,
        tier=1,
        env_keys=["KIPRIS_API_KEY"],
        base_url="http://plus.kipris.or.kr/openapi/rest/design",
        default_license="KR-Government-Open",
        requires_auth=True,
    ),
    # Tier 2 - License metadata required
    "flickr": ProviderConfig(
        adapter_class=FlickrAdapter,
        tier=2,
        env_keys=["FLICKR_API_KEY"],
        base_url="https://www.flickr.com/services/api",
        default_license="(CC-filtered)",
        requires_auth=True,
    ),
    "internet_archive": ProviderConfig(
        adapter_class=InternetArchiveAdapter,
        tier=2,
        env_keys=[],
        base_url="https://archive.org/advancedsearch.php",
        default_license="(per-item PD/CC)",
        requires_auth=False,
    ),
    "web_search": ProviderConfig(
        adapter_class=WebSearchAdapter,
        tier=2,
        env_keys=["SERPAPI_KEY", "BING_SEARCH_KEY"],  # One of these
        base_url="",
        default_license="(usage_rights filter)",
        requires_auth=True,
    ),
    # Tier 3 - External links only
    "youtube_thumbnail": ProviderConfig(
        adapter_class=YouTubeThumbnailAdapter,
        tier=3,
        env_keys=["YOUTUBE_API_KEYS"],
        base_url="https://www.googleapis.com/youtube/v3",
        default_license="(video-specific)",
        requires_auth=True,
    ),
}


class AdapterRegistry:
    """Registry for managing image search adapters.

    Provides data-driven access to providers without if/elif branching.
    """

    def __init__(self):
        """Initialize registry."""
        self._adapters: dict[str, ImageSearchPort] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all available providers.

        Only initializes providers whose API keys are configured.
        """
        if self._initialized:
            return

        logger.info("Initializing image search adapter registry...")

        for provider_id, config in PROVIDER_REGISTRY.items():
            if config.adapter_class is None:
                logger.debug(f"Skipping {provider_id}: adapter not implemented")
                continue

            # Check if required API keys are present
            if config.requires_auth and config.env_keys:
                # For web_search, at least one key is required
                if provider_id == "web_search":
                    has_key = any(os.getenv(key) for key in config.env_keys)
                else:
                    has_key = all(os.getenv(key) for key in config.env_keys)

                if not has_key:
                    logger.debug(f"Skipping {provider_id}: API keys not configured")
                    continue

            try:
                adapter = config.adapter_class()
                if adapter.is_available():
                    self._adapters[provider_id] = adapter
                    logger.info(f"Initialized adapter: {provider_id}")
                else:
                    logger.debug(f"Provider {provider_id} not available")

            except Exception as e:
                logger.warning(f"Failed to initialize {provider_id}: {e}")

        self._initialized = True
        logger.info(f"Registry initialized with {len(self._adapters)} providers")

    def get_provider(self, provider_id: str) -> ImageSearchPort | None:
        """Get specific provider adapter by ID.

        Args:
            provider_id: Provider identifier

        Returns:
            Adapter instance or None if not found
        """
        if not self._initialized:
            logger.warning("Registry not initialized, call initialize() first")
            return None

        return self._adapters.get(provider_id)

    def get_active_providers(self) -> dict[str, ImageSearchPort]:
        """Get all active (initialized) providers.

        Returns:
            Dict of provider_id -> adapter
        """
        if not self._initialized:
            logger.warning("Registry not initialized, call initialize() first")
            return {}

        return self._adapters.copy()

    def get_providers_by_tier(self, tier: int) -> list[ImageSearchPort]:
        """Get all active providers for a given tier.

        Args:
            tier: Provider tier (1, 2, or 3)

        Returns:
            List of adapters
        """
        if not self._initialized:
            logger.warning("Registry not initialized, call initialize() first")
            return []

        return [
            adapter
            for provider_id, adapter in self._adapters.items()
            if adapter.get_tier() == tier
        ]

    def get_provider_config(self, provider_id: str) -> ProviderConfig | None:
        """Get provider configuration from registry.

        Args:
            provider_id: Provider identifier

        Returns:
            Provider config or None if not found
        """
        return PROVIDER_REGISTRY.get(provider_id)

    async def shutdown(self) -> None:
        """Shutdown all adapters and close HTTP clients."""
        logger.info("Shutting down adapter registry...")

        for provider_id, adapter in self._adapters.items():
            try:
                if isinstance(adapter, ImageSearchAdapter) and hasattr(adapter, "_client"):
                    await adapter._client.aclose()
                logger.debug(f"Closed adapter: {provider_id}")
            except Exception as e:
                logger.warning(f"Error closing {provider_id}: {e}")

        self._adapters.clear()
        self._initialized = False
        logger.info("Registry shutdown complete")


# Global registry instance
_registry: AdapterRegistry | None = None


async def get_registry() -> AdapterRegistry:
    """Get or create global registry instance.

    Returns:
        Global adapter registry
    """
    global _registry

    if _registry is None:
        _registry = AdapterRegistry()
        await _registry.initialize()

    return _registry
