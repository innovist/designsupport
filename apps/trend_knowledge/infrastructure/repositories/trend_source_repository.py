"""Django ORM repository for TrendSource entities.

Implements TrendSourceRepositoryPort using Django models.
"""
from logging import getLogger
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import TrendSourceRepositoryPort
from apps.trend_knowledge.domain.entities import TrendSource, TrendSourceType

logger = getLogger(__name__)


class DjangoTrendSourceRepository(TrendSourceRepositoryPort):
    """Django ORM repository for TrendSource."""

    async def save(self, source: TrendSource) -> TrendSource:
        """Save a trend source.

        Args:
            source: TrendSource entity to save

        Returns:
            Saved TrendSource entity

        Raises:
            RuntimeError: If Django models not available
        """
        try:
            from apps.trend_knowledge.models import TrendSource as TrendSourceModel

            # Convert entity to model
            model_data = {
                "id": source.id,
                "url": source.url,
                "source_type": source.source_type.value,
                "domain": source.domain,
                "name": source.name,
                "config": source.config,
                "is_active": source.is_active,
                "created_at": source.created_at,
                "updated_at": source.updated_at,
            }

            # Create or update
            model, created = TrendSourceModel.objects.update_or_create(
                id=source.id,
                defaults=model_data,
            )

            logger.info(f"Saved TrendSource: {model.id} (created: {created})")

            # Convert back to entity
            return self._model_to_entity(model)

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            raise RuntimeError("Django models not available") from e

    async def get_by_id(self, source_id: UUID) -> TrendSource | None:
        """Get source by ID.

        Args:
            source_id: Source UUID

        Returns:
            TrendSource entity or None
        """
        try:
            from apps.trend_knowledge.models import TrendSource as TrendSourceModel

            model = TrendSourceModel.objects.filter(id=source_id).first()
            if model:
                return self._model_to_entity(model)
            return None

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return None

    async def list_active(
        self,
        domain: str | None = None,
        limit: int = 100,
    ) -> list[TrendSource]:
        """List active sources.

        Args:
            domain: Optional domain filter
            limit: Maximum results

        Returns:
            List of TrendSource entities
        """
        try:
            from apps.trend_knowledge.models import TrendSource as TrendSourceModel

            queryset = TrendSourceModel.objects.filter(is_active=True)
            if domain:
                queryset = queryset.filter(domain=domain)

            models = queryset[:limit]
            return [self._model_to_entity(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    async def update(self, source: TrendSource) -> TrendSource:
        """Update an existing source.

        Args:
            source: TrendSource entity with updates

        Returns:
            Updated TrendSource entity
        """
        return await self.save(source)

    def _model_to_entity(self, model: Any) -> TrendSource:
        """Convert Django model to domain entity.

        Args:
            model: Django TrendSource model

        Returns:
            TrendSource domain entity
        """
        return TrendSource(
            id=model.id,
            url=model.url,
            source_type=TrendSourceType(model.source_type),
            domain=model.domain,
            name=model.name,
            config=model.config,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
