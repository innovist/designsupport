"""Django management command to seed taxonomy data.

Implements initial 7 categories per SPEC-02 across 4 domains.
Idempotent - won't duplicate on re-run.

Usage:
    python manage.py seed_taxonomy
"""
from django.core.management.base import BaseCommand

from apps.trend_knowledge.infrastructure.management.seed_data import (
    get_initial_categories,
    get_sample_sources,
)
from apps.trend_knowledge.infrastructure.management.seeder import (
    TaxonomySeeder,
)


class Command(BaseCommand):
    """Seed initial taxonomy data and sample trend sources."""

    help = "Seed initial taxonomy categories and sample trend sources"

    def handle(self, *args, **options):
        """Execute seeding command."""
        import asyncio

        # Run async seeder
        asyncio.run(self._seed())

    async def _seed(self):
        """Execute async seeding."""
        self.stdout.write(self.style.SUCCESS("Starting taxonomy seeding..."))

        # Initialize seeder
        seeder = TaxonomySeeder()

        # Seed taxonomy categories
        taxonomy_result = await seeder.seed_taxonomy()
        self.stdout.write(
            self.style.SUCCESS(
                f"Taxonomy seeding complete: {taxonomy_result['created']} created, "
                f"{taxonomy_result['skipped']} skipped"
            )
        )

        # Seed sample sources
        self.stdout.write(self.style.SUCCESS("\nSeeding sample trend sources..."))
        source_result = await seeder.seed_sources()
        self.stdout.write(
            self.style.SUCCESS(
                f"Source seeding complete: {source_result['created']} created, "
                f"{source_result['skipped']} skipped"
            )
        )
