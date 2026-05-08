"""Taxonomy seeder for initial data population.

Implements idempotent seeding logic for taxonomy and sources.
"""
from apps.trend_knowledge.domain.entities import (
    TrendSource,
    TrendTaxonomy,
)
from apps.trend_knowledge.infrastructure.repositories import (
    DjangoTrendSourceRepository,
    DjangoTrendTaxonomyRepository,
)
from apps.trend_knowledge.infrastructure.management.seed_data import (
    get_initial_categories,
    get_sample_sources,
)


class TaxonomySeeder:
    """Seeder for taxonomy categories and trend sources."""

    def __init__(self):
        """Initialize seeder with repositories."""
        self._taxonomy_repo = DjangoTrendTaxonomyRepository()
        self._source_repo = DjangoTrendSourceRepository()

    async def seed_taxonomy(self) -> dict:
        """Seed taxonomy categories.

        Returns:
            Dictionary with created and skipped counts
        """
        initial_categories = get_initial_categories()

        created_count = 0
        skipped_count = 0

        for domain, categories in initial_categories.items():
            for category_data in categories:
                # Check if already exists
                existing = await self._find_existing_taxonomy(
                    domain,
                    category_data["category"],
                )

                if existing:
                    skipped_count += 1
                    print(f"  ✓ Skipped existing: {domain}/{category_data['category']}")
                    continue

                # Create new taxonomy entry
                taxonomy = TrendTaxonomy(
                    domain=domain,
                    category=category_data["category"],
                    label=category_data["label"],
                    description=category_data["description"],
                    active=True,
                )

                await self._taxonomy_repo.save(taxonomy)
                created_count += 1

                print(
                    f"  + Created: {domain}/{category_data['category']} - {category_data['label']}"
                )

        return {
            "created": created_count,
            "skipped": skipped_count,
        }

    async def seed_sources(self) -> dict:
        """Seed sample trend sources.

        Returns:
            Dictionary with created and skipped counts
        """
        sample_sources = get_sample_sources()

        created_count = 0
        skipped_count = 0

        for source_data in sample_sources:
            # Check if URL already exists
            existing = await self._find_existing_source(source_data["url"])

            if existing:
                skipped_count += 1
                print(f"  ✓ Skipped existing source: {source_data['name']}")
                continue

            # Create new source
            source = TrendSource(
                name=source_data["name"],
                url=source_data["url"],
                domain=source_data["domain"],
                crawl_schedule=source_data["crawl_schedule"],
                trust_level=source_data["trust_level"],
                license=source_data["license"],
                active=source_data.get("active", True),
            )

            await self._source_repo.save(source)
            created_count += 1

            print(f"  + Created source: {source_data['name']}")

        return {
            "created": created_count,
            "skipped": skipped_count,
        }

    async def _find_existing_taxonomy(
        self,
        domain: str,
        category: str,
    ) -> TrendTaxonomy | None:
        """Check if taxonomy entry already exists.

        Args:
            domain: Domain category
            category: Category name

        Returns:
            Existing taxonomy or None
        """
        # List all active taxonomies for domain
        taxonomies = await self._taxonomy_repo.list_active(domain=domain)

        # Check for matching category
        for taxonomy in taxonomies:
            if taxonomy.category == category:
                return taxonomy

        return None

    async def _find_existing_source(
        self,
        url: str,
    ) -> TrendSource | None:
        """Check if source already exists by URL.

        Args:
            url: Source URL

        Returns:
            Existing source or None
        """
        # List all active sources and filter by URL
        sources = await self._source_repo.list_active(limit=1000)

        for source in sources:
            if source.url == url:
                return source

        return None
