"""Quota repository implementation.

Manages persistence of ImageProviderQuota entities.
"""
from datetime import datetime, timezone, timedelta
from logging import getLogger
from typing import Optional

from apps.references.domain.entities import ImageProviderQuota
from apps.references.application.ports import QuotaRepositoryPort
from apps.references.infrastructure.orm.models import ImageProviderQuota as ImageProviderQuotaModel

logger = getLogger(__name__)


class QuotaRepository(QuotaRepositoryPort):
    """Django ORM repository for ImageProviderQuota entities."""

    async def get_quota(self, provider: str) -> Optional[ImageProviderQuota]:
        """Get quota record for provider.

        Args:
            provider: Provider identifier

        Returns:
            Quota entity or None if not found
        """
        try:
            model = await ImageProviderQuotaModel.objects.aget(provider=provider)
            return self._model_to_entity(model)
        except ImageProviderQuotaModel.DoesNotExist:
            return None

    async def save_quota(self, quota: ImageProviderQuota) -> ImageProviderQuota:
        """Save or update quota record.

        Args:
            quota: Quota entity to save

        Returns:
            Saved quota entity
        """
        try:
            model = await ImageProviderQuotaModel.objects.aget(provider=quota.provider)

            # Update existing
            model.daily_limit = quota.daily_limit
            model.used_today = quota.used_today
            model.reset_at = quota.reset_at
            model.active = quota.active
            model.last_error_at = quota.last_error_at

        except ImageProviderQuotaModel.DoesNotExist:
            # Create new
            model = await ImageProviderQuotaModel.objects.acreate(
                provider=quota.provider,
                daily_limit=quota.daily_limit,
                used_today=quota.used_today,
                reset_at=quota.reset_at,
                active=quota.active,
                last_error_at=quota.last_error_at,
            )

        await model.asave()
        return self._model_to_entity(model)

    async def check_and_increment(self, provider: str) -> bool:
        """Check if provider can make a call and increment usage.

        Args:
            provider: Provider identifier

        Returns:
            True if call allowed, False if quota exceeded
        """
        try:
            model = await ImageProviderQuotaModel.objects.select_for_update().aget(provider=provider)

            # Check if reset needed
            if datetime.now(timezone.utc) >= model.reset_at:
                model.used_today = 0
                # Update reset time to next day
                model.reset_at = model.reset_at + timedelta(days=1)

            # Check quota
            if model.used_today >= model.daily_limit:
                logger.warning(f"Provider {provider} quota exceeded: {model.used_today}/{model.daily_limit}")
                return False

            # Increment usage
            model.used_today += 1
            await model.asave()

            return True

        except ImageProviderQuotaModel.DoesNotExist:
            # Create with default limits if not exists
            quota = ImageProviderQuota(
                provider=provider,
                daily_limit=1000,  # Default
                used_today=1,  # First call
                reset_at=datetime.now(timezone.utc) + timedelta(days=1),
                active=True,
                last_error_at=None,
            )
            await self.save_quota(quota)
            return True

    async def reset_daily_counters(self) -> None:
        """Reset daily counters for providers that need reset."""
        now = datetime.now(timezone.utc)

        # Find all providers that need reset
        models_to_reset = ImageProviderQuotaModel.objects.filter(
            reset_at__lte=now,
            used_today__gt=0,
        )

        count = 0
        async for model in models_to_reset:
            model.used_today = 0
            # Update reset time to next day
            model.reset_at = model.reset_at + timedelta(days=1)
            await model.asave()
            count += 1

        if count > 0:
            logger.info(f"Reset daily counters for {count} providers")

    def _model_to_entity(self, model: ImageProviderQuotaModel) -> ImageProviderQuota:
        """Convert ORM model to domain entity.

        Args:
            model: ORM model instance

        Returns:
            Domain entity
        """
        return ImageProviderQuota(
            provider=model.provider,
            daily_limit=model.daily_limit,
            used_today=model.used_today,
            reset_at=model.reset_at,
            active=model.active,
            last_error_at=model.last_error_at,
        )
