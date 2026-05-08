"""Seed data for trend knowledge taxonomy.

Initial taxonomy categories as DATA (not hardcoded constants).
Admin can deactivate/extend categories via console.
"""
import logging
from uuid import uuid4

from apps.trend_knowledge.domain.entities import TrendTaxonomy
from apps.trend_knowledge.infrastructure.repositories import (
    DjangoTrendTaxonomyRepository,
)

logger = logging.getLogger(__name__)


# Initial taxonomy categories per domain
# These are seed data records, NOT code constants
INITIAL_TAXONOMY = {
    "industrial": [
        ("nature", "Nature", "Natural materials, sustainable design, biophilic patterns"),
        ("product", "Product", "Industrial product design, manufacturing, materials"),
        ("architecture", "Architecture", "Building design, urban planning, structural trends"),
        ("fashion", "Fashion", "Textile industry, wearable technology, smart fabrics"),
        ("graphic", "Graphic", "Visual communication, branding, packaging design"),
        ("advertising", "Advertising", "Marketing campaigns, consumer behavior, media trends"),
        ("material", "Material", "Advanced materials, composites, smart materials"),
    ],
    "fashion": [
        ("nature", "Nature", "Organic materials, natural dyes, sustainable fashion"),
        ("product", "Product", "Apparel design, accessories, footwear"),
        ("architecture", "Architecture", "Retail space design, pop-up stores, fashion weeks"),
        ("fashion", "Fashion", "Haute couture, ready-to-wear, streetwear"),
        ("graphic", "Graphic", "Fashion photography, lookbooks, visual merchandising"),
        ("advertising", "Advertising", "Fashion marketing, influencer trends, social media"),
        ("material", "Material", "Fabrics, textiles, innovative materials"),
    ],
    "visual": [
        ("nature", "Nature", "Natural landscapes, environmental graphics, eco-design"),
        ("product", "Product", "Product visualization, 3D design, packaging"),
        ("architecture", "Architecture", "Interior design, spatial design, wayfinding"),
        ("fashion", "Fashion", "Fashion illustration, textile patterns, color trends"),
        ("graphic", "Graphic", "Typography, layout design, digital graphics"),
        ("advertising", "Advertising", "Visual campaigns, motion graphics, video trends"),
        ("material", "Material", "Surface design, texture, material visualizations"),
    ],
    "advertising": [
        ("nature", "Nature", "Green marketing, sustainability messaging, eco-branding"),
        ("product", "Product", "Product advertising, launches, brand positioning"),
        ("architecture", "Architecture", "Retail advertising, experiential marketing"),
        ("fashion", "Fashion", "Fashion campaigns, brand collaborations, endorsements"),
        ("graphic", "Graphic", "Print design, digital ads, social media graphics"),
        ("advertising", "Advertising", "Campaign strategies, consumer insights, media trends"),
        ("material", "Material", "Product material advertising, sustainability claims"),
    ],
}


async def seed_taxonomy_data() -> None:
    """Seed initial taxonomy categories.

    Creates 7 categories for each of 4 domains (28 total).
    Only creates if taxonomy table is empty.

    Note:
        These are seed data records stored in the database.
        Admin can deactivate/extend via console - NOT hardcoded constants.
    """
    try:
        repo = DjangoTrendTaxonomyRepository()

        # Check if already seeded
        existing = await repo.list_active()
        if existing:
            logger.info(f"Taxonomy already seeded with {len(existing)} categories")
            return

        # Seed initial categories
        created_count = 0
        for domain, categories in INITIAL_TAXONOMY.items():
            for category, label, description in categories:
                taxonomy = TrendTaxonomy(
                    domain=domain,
                    category=category,
                    label=label,
                    description=description,
                    parent_id=None,  # Top-level categories
                    active=True,
                )

                await repo.save(taxonomy)
                created_count += 1

        logger.info(f"Seeded {created_count} taxonomy categories across {len(INITIAL_TAXONOMY)} domains")

    except Exception as e:
        logger.error(f"Failed to seed taxonomy data: {e}")
        raise


def get_seed_taxonomy_count() -> int:
    """Get total number of seed taxonomy categories.

    Returns:
        Total count of seed categories
    """
    count = 0
    for categories in INITIAL_TAXONOMY.values():
        count += len(categories)
    return count
