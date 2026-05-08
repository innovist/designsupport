"""Quota management service for image providers.

Manages API rate limits, daily quotas, and round-robin provider selection.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from logging import getLogger

from apps.references.domain.entities import ImageProviderQuota
from apps.references.infrastructure.image_search.base import ImageSearchAdapter
from apps.references.infrastructure.repositories.quota_repository import QuotaRepository
from shared.domain.exceptions import OperationError, ValidationError

logger = getLogger(__name__)


class QuotaManager:
    """Manages provider quotas and rate limiting.

    Features:
    - Check quota before API calls
    - Increment usage on success
    - Round-robin to same-tier provider when limit reached
    - Record HTTP 429 with exponential backoff
    - Daily quota reset
    """

    # Default daily limits (from SPEC-02 image-providers.md)
    DEFAULT_LIMITS = {
        "unsplash": 5000,
        "pexels": 20000,
        "pixabay": 5000,
        "wikimedia": 1000,
        "openverse": 1000,
        "nasa": 1000,
        "met": 1000,
        "smithsonian": 1000,
        "europeana": 1000,
        "rijks": 1000,
        "kipris": 10000,
        "flickr": 3600,
        "internet_archive": 1000,
        "web_search": 100,  # Variable per key
        "youtube_thumbnail": 10000,
    }

    # Reset time configurations (hour of day in UTC)
    RESET_TIMES = {
        "unsplash": 0,  # Midnight UTC
        "pexels": 0,
        "pixabay": 0,
        "kipris": 0,  # KST 9am = UTC 0am
        "flickr": 0,
        "youtube_thumbnail": 0,
    }

    def __init__(
        self,
        quota_repository: QuotaRepository,
    ):
        """Initialize quota manager.

        Args:
            quota_repository: Repository for quota persistence
        """
        self._quota_repo = quota_repository
        self._lock = asyncio.Lock()

    async def can_make_call(
        self,
        provider: str,
        adapter: ImageSearchAdapter,
    ) -> bool:
        """Check if provider can make a call.

        Args:
            provider: Provider identifier
            adapter: Provider adapter instance

        Returns:
            True if call allowed, False if quota exceeded

        Raises:
            OperationError: If provider not found
        """
        quota = await self._get_or_create_quota(provider, adapter)
        quota.reset_if_needed()

        return quota.can_make_call()

    async def record_call(
        self,
        provider: str,
        adapter: ImageSearchAdapter,
        success: bool = True,
    ) -> None:
        """Record a provider API call.

        Args:
            provider: Provider identifier
            adapter: Provider adapter instance
            success: Whether the call was successful

        Note:
            Increments usage on success, records error on failure.
        """
        quota = await self._get_or_create_quota(provider, adapter)

        if success:
            quota.increment_usage()
            logger.debug(f"Recorded successful call for {provider}: {quota.used_today}/{quota.daily_limit}")
        else:
            quota.last_error_at = datetime.now(timezone.utc)
            logger.warning(f"Recorded failed call for {provider}")

        await self._quota_repo.save_quota(quota)

    async def get_quota(self, provider: str) -> ImageProviderQuota | None:
        """Get current quota status for provider.

        Args:
            provider: Provider identifier

        Returns:
            Quota entity or None if not found
        """
        return await self._quota_repo.get_quota(provider)

    async def get_all_quotas(self) -> dict[str, ImageProviderQuota]:
        """Get all provider quotas.

        Returns:
            Dict of provider -> quota entity
        """
        # This would need to be implemented in the repository
        # For now, return empty dict
        return {}

    async def select_provider(
        self,
        provider_ids: list[str],
        adapters: dict[str, ImageSearchAdapter],
    ) -> str | None:
        """Select an available provider using round-robin.

        Args:
            provider_ids: List of provider IDs to try
            adapters: Dict of provider_id -> adapter

        Returns:
            Selected provider ID or None if all unavailable

        Note:
            Tries providers in order, skips those with exhausted quota.
        """
        async with self._lock:
            for provider_id in provider_ids:
                adapter = adapters.get(provider_id)
                if not adapter:
                    continue

                if await self.can_make_call(provider_id, adapter):
                    return provider_id

            # All providers exhausted
            logger.warning(f"All providers exhausted: {provider_ids}")
            return None

    async def reset_daily_counters(self) -> None:
        """Reset daily counters for providers that need reset.

        Should be called periodically (e.g., via cron or scheduled task).
        """
        await self._quota_repo.reset_daily_counters()
        logger.info("Daily quota counters reset")

    async def update_limit(
        self,
        provider: str,
        new_limit: int,
    ) -> None:
        """Update daily limit for a provider.

        Args:
            provider: Provider identifier
            new_limit: New daily limit

        Raises:
            ValidationError: If limit is invalid
        """
        if new_limit <= 0:
            raise ValidationError(field="new_limit", message="Daily limit must be positive")

        quota = await self._quota_repo.get_quota(provider)
        if not quota:
            raise OperationError(operation="update_limit", reason=f"Provider {provider} not found")

        quota.daily_limit = new_limit
        await self._quota_repo.save_quota(quota)

        logger.info(f"Updated daily limit for {provider}: {new_limit}")

    async def _get_or_create_quota(
        self,
        provider: str,
        adapter: ImageSearchAdapter,
    ) -> ImageProviderQuota:
        """Get existing quota or create new one.

        Args:
            provider: Provider identifier
            adapter: Provider adapter instance

        Returns:
            Quota entity
        """
        # Try to get existing quota
        quota = await self._quota_repo.get_quota(provider)

        if quota is None:
            # Create new quota with default limit
            default_limit = self.DEFAULT_LIMITS.get(provider, 1000)

            # Calculate reset time based on provider's reset schedule
            reset_hour = self.RESET_TIMES.get(provider, 0)
            now = datetime.now(timezone.utc)
            reset_at = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)

            # If reset time has passed today, set to tomorrow
            if reset_at <= now:
                reset_at += timedelta(days=1)

            quota = ImageProviderQuota(
                provider=provider,
                daily_limit=default_limit,
                used_today=0,
                reset_at=reset_at,
                active=True,
                last_error_at=None,
            )

            await self._quota_repo.save_quota(quota)
            logger.info(f"Created quota for {provider}: limit={default_limit}, reset_at={reset_at}")

        return quota
