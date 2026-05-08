"""Django ORM repository for TrendTaxonomy entities.

Implements TrendTaxonomyRepositoryPort using Django models.
"""
from logging import getLogger
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import TrendTaxonomyRepositoryPort
from apps.trend_knowledge.domain.entities import TrendTaxonomy

logger = getLogger(__name__)


class DjangoTrendTaxonomyRepository(TrendTaxonomyRepositoryPort):
    """Django ORM repository for TrendTaxonomy.

    Data-driven taxonomy - NO hardcoded categories.
    All categories managed via database and seed data.
    """

    async def save(self, taxonomy: TrendTaxonomy) -> TrendTaxonomy:
        """Save a taxonomy category.

        Args:
            taxonomy: TrendTaxonomy entity to save

        Returns:
            Saved TrendTaxonomy entity

        Raises:
            RuntimeError: If Django models not available
        """
        try:
            from apps.trend_knowledge.infrastructure.orm.models import (
                TrendTaxonomy as TrendTaxonomyModel,
            )

            # Convert entity to model
            model_data = {
                "id": taxonomy.id,
                "domain": taxonomy.domain,
                "category": taxonomy.category,
                "label": taxonomy.label,
                "description": taxonomy.description,
                "parent_id": taxonomy.parent_id,
                "active": taxonomy.active,
                "created_at": taxonomy.created_at,
                "updated_at": taxonomy.updated_at,
            }

            # Create or update
            model, created = TrendTaxonomyModel.objects.update_or_create(
                id=taxonomy.id,
                defaults=model_data,
            )

            logger.info(f"Saved TrendTaxonomy: {model.id} (created: {created})")

            # Convert back to entity
            return self._model_to_entity(model)

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            raise RuntimeError("Django models not available") from e

    async def list_active(
        self,
        domain: str | None = None,
    ) -> list[TrendTaxonomy]:
        """List active taxonomy categories.

        Args:
            domain: Optional domain filter

        Returns:
            List of TrendTaxonomy entities
        """
        try:
            from apps.trend_knowledge.infrastructure.orm.models import (
                TrendTaxonomy as TrendTaxonomyModel,
            )

            queryset = TrendTaxonomyModel.objects.filter(active=True)
            if domain:
                queryset = queryset.filter(domain=domain)

            models = queryset.all()
            return [self._model_to_entity(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    async def get_by_id(self, taxonomy_id: UUID) -> TrendTaxonomy | None:
        """Get taxonomy by ID.

        Args:
            taxonomy_id: Taxonomy UUID

        Returns:
            TrendTaxonomy entity or None
        """
        try:
            from apps.trend_knowledge.infrastructure.orm.models import (
                TrendTaxonomy as TrendTaxonomyModel,
            )

            model = TrendTaxonomyModel.objects.filter(id=taxonomy_id).first()
            if model:
                return self._model_to_entity(model)
            return None

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return None

    def _model_to_entity(self, model: Any) -> TrendTaxonomy:
        """Convert Django model to domain entity.

        Args:
            model: Django TrendTaxonomy model

        Returns:
            TrendTaxonomy domain entity
        """
        return TrendTaxonomy(
            id=model.id,
            domain=model.domain,
            category=model.category,
            label=model.label,
            description=model.description,
            parent_id=model.parent_id,
            active=model.active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
