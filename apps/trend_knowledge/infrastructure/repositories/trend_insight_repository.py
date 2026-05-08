"""Django ORM repository for TrendInsight entities.

Implements TrendInsightRepositoryPort using Django models.
"""
from logging import getLogger
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import TrendInsightRepositoryPort
from apps.trend_knowledge.domain.entities import TrendInsight

logger = getLogger(__name__)


# @MX:ANCHOR: [AUTO] TrendInsight persistence layer with search capabilities
# @MX:REASON: Core data access for RAG pipeline; used by insight extraction and search workflows
class DjangoTrendInsightRepository(TrendInsightRepositoryPort):
    """Django ORM repository for TrendInsight."""

    async def save(self, insight: TrendInsight) -> TrendInsight:
        """Save a trend insight.

        Args:
            insight: TrendInsight entity to save

        Returns:
            Saved TrendInsight entity

        Raises:
            RuntimeError: If Django models not available
        """
        try:
            from apps.trend_knowledge.models import TrendInsight as TrendInsightModel

            # Convert entity to model
            model_data = {
                "id": insight.id,
                "document_id": insight.document_id,
                "summary": insight.summary,
                "keywords": insight.keywords,
                "evidence_quote": insight.evidence_quote,
                "confidence": insight.confidence,
                "created_at": insight.created_at,
            }

            # Create or update
            model, created = TrendInsightModel.objects.update_or_create(
                id=insight.id,
                defaults=model_data,
            )

            logger.info(f"Saved TrendInsight: {model.id} (created: {created})")

            # Convert back to entity
            return self._model_to_entity(model)

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            raise RuntimeError("Django models not available") from e

    async def search(
        self,
        query: str,
        domain: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 10,
    ) -> list[TrendInsight]:
        """Search insights by query text and filters.

        Args:
            query: Search query text
            domain: Optional domain filter
            min_confidence: Minimum confidence score
            limit: Maximum results

        Returns:
            List of TrendInsight entities
        """
        try:
            from apps.trend_knowledge.models import TrendInsight as TrendInsightModel
            from django.db.models import Q

            # Build query
            queryset = TrendInsightModel.objects.filter(
                confidence__gte=min_confidence,
            )

            # Text search (simple LIKE for now, replace with full-text search later)
            queryset = queryset.filter(
                Q(summary__icontains=query) | Q(keywords__icontains=query)
            )

            # Domain filter via source
            if domain:
                queryset = queryset.filter(
                    document__source__domain=domain,
                )

            models = queryset[:limit]
            return [self._model_to_entity(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    async def get_by_document(self, document_id: UUID) -> list[TrendInsight]:
        """Get all insights for a document.

        Args:
            document_id: Document UUID

        Returns:
            List of TrendInsight entities
        """
        try:
            from apps.trend_knowledge.models import TrendInsight as TrendInsightModel

            models = TrendInsightModel.objects.filter(
                document_id=document_id,
            )

            return [self._model_to_entity(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    def _model_to_entity(self, model: Any) -> TrendInsight:
        """Convert Django model to domain entity.

        Args:
            model: Django TrendInsight model

        Returns:
            TrendInsight domain entity
        """
        return TrendInsight(
            id=model.id,
            document_id=model.document_id,
            summary=model.summary,
            keywords=model.keywords,
            evidence_quote=model.evidence_quote,
            confidence=model.confidence,
            created_at=model.created_at,
        )
