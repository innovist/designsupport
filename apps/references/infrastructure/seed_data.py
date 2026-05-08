"""Seed data for references app.

Creates default ImageProviderQuota records with daily limits from SPEC-02.
"""
from datetime import datetime, timezone, timedelta
from logging import getLogger

from django.core.management.base import BaseCommand
from apps.references.infrastructure.orm.models import ImageProviderQuotaModel

logger = getLogger(__name__)


class Command(BaseCommand):
    """Django management command to seed reference data."""

    help = "Seed default provider quotas from SPEC-02 configuration"

    def handle(self, *args, **options):
        """Execute seed command."""
        self.stdout.write("Seeding ImageProviderQuota data...")

        # Default daily limits from SPEC-02 image-providers.md
        providers = [
            # Tier 1
            {"provider": "unsplash", "daily_limit": 5000},
            {"provider": "pexels", "daily_limit": 20000},
            {"provider": "pixabay", "daily_limit": 5000},
            {"provider": "wikimedia", "daily_limit": 1000},
            {"provider": "openverse", "daily_limit": 1000},
            {"provider": "nasa", "daily_limit": 1000},
            {"provider": "met", "daily_limit": 1000},
            {"provider": "smithsonian", "daily_limit": 1000},
            {"provider": "europeana", "daily_limit": 1000},
            {"provider": "rijks", "daily_limit": 1000},
            {"provider": "kipris", "daily_limit": 10000},
            # Tier 2
            {"provider": "flickr", "daily_limit": 3600},
            {"provider": "internet_archive", "daily_limit": 1000},
            {"provider": "web_search", "daily_limit": 100},
            # Tier 3
            {"provider": "youtube_thumbnail", "daily_limit": 10000},
        ]

        # Calculate reset time (tomorrow at midnight UTC)
        now = datetime.now(timezone.utc)
        reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        created = 0
        updated = 0

        for provider_config in providers:
            provider = provider_config["provider"]
            daily_limit = provider_config["daily_limit"]

            # Use get_or_create to avoid duplicates
            obj, created_flag = ImageProviderQuotaModel.objects.get_or_create(
                provider=provider,
                defaults={
                    "daily_limit": daily_limit,
                    "used_today": 0,
                    "reset_at": reset_at,
                    "active": True,
                    "last_error_at": None,
                },
            )

            if created_flag:
                created += 1
                self.stdout.write(f"  Created: {provider} (limit={daily_limit})")
            else:
                # Update limit if different
                if obj.daily_limit != daily_limit:
                    obj.daily_limit = daily_limit
                    obj.save()
                    updated += 1
                    self.stdout.write(f"  Updated: {provider} (limit={daily_limit})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding complete: {created} created, {updated} updated"
            )
        )
