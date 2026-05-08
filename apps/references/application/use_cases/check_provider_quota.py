"""Check provider quota use case.

Checks and updates daily limits, suggests alternative providers.
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

from apps.references.application.dtos import ReferenceAssetDTO
from shared.domain.exceptions import ValidationError

logger = getLogger(__name__)


class CheckProviderQuotaUseCase:
    """Check and manage provider API quotas."""

    def __init__(
        self,
        quota_store: dict[str, Any],  # Provider -> quota tracking
        daily_limits: dict[str, int],  # Provider -> daily limit
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            quota_store: Storage for quota tracking (in-memory or Redis)
            daily_limits: Daily request limits per provider
        """
        self._quota_store = quota_store
        self._daily_limits = daily_limits

    async def execute(
        self,
        provider: str,
        requested: int = 1,
    ) -> dict[str, Any]:
        """Check quota for a provider and suggest alternatives if needed.

        Args:
            provider: Provider name to check
            requested: Number of requests being made

        Returns:
            Quota status with remaining count and alternatives

        Raises:
            ValidationError: If provider is unknown
        """
        if provider not in self._daily_limits:
            raise ValidationError(f"Unknown provider: {provider}", field="provider")

        today = datetime.now(timezone.utc).date()
        daily_limit = self._daily_limits[provider]

        # Get or initialize quota tracking
        quota_key = f"{provider}:{today}"
        used = self._quota_store.get(quota_key, 0)
        remaining = daily_limit - used

        logger.info(
            f"Quota check for {provider}: {used}/{daily_limit} used, {remaining} remaining"
        )

        # Check if quota available
        has_quota = remaining >= requested
        alternatives = []

        if not has_quota:
            # Suggest alternative providers
            for alt_provider, alt_limit in self._daily_limits.items():
                if alt_provider == provider:
                    continue
                alt_key = f"{alt_provider}:{today}"
                alt_used = self._quota_store.get(alt_key, 0)
                alt_remaining = alt_limit - alt_used
                if alt_remaining >= requested:
                    alternatives.append({
                        "provider": alt_provider,
                        "remaining": alt_remaining,
                    })

            logger.warning(
                f"Quota exceeded for {provider}. "
                f"Alternatives: {[a['provider'] for a in alternatives]}"
            )

        return {
            "provider": provider,
            "daily_limit": daily_limit,
            "used": used,
            "remaining": remaining,
            "has_quota": has_quota,
            "alternatives": alternatives,
        }

    async def record_usage(
        self,
        provider: str,
        count: int = 1,
    ) -> None:
        """Record API usage for a provider.

        Args:
            provider: Provider name
            count: Number of requests to record
        """
        today = datetime.now(timezone.utc).date()
        quota_key = f"{provider}:{today}"

        current = self._quota_store.get(quota_key, 0)
        self._quota_store[quota_key] = current + count

        logger.info(f"Recorded {count} requests for {provider}. Total: {current + count}")
