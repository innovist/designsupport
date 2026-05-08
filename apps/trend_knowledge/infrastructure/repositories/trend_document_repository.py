"""Django ORM repository for TrendDocument entities.

Implements TrendDocumentRepositoryPort using Django models.
"""
from logging import getLogger
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import TrendDocumentRepositoryPort
from apps.trend_knowledge.domain.entities import TrendDocument, TrendDocumentStatus

logger = getLogger(__name__)


class DjangoTrendDocumentRepository(TrendDocumentRepositoryPort):
    """Django ORM repository for TrendDocument."""

    async def save(self, document: TrendDocument) -> TrendDocument:
        """Save a trend document.

        Args:
            document: TrendDocument entity to save

        Returns:
            Saved TrendDocument entity

        Raises:
            RuntimeError: If Django models not available
        """
        try:
            from apps.trend_knowledge.models import TrendDocument as TrendDocumentModel

            # Convert entity to model
            model_data = {
                "id": document.id,
                "source_id": document.source_id,
                "title": document.title,
                "url": document.url,
                "published_at": document.published_at,
                "collected_at": document.collected_at,
                "raw_uri": document.raw_uri,
                "parsed_text_uri": document.parsed_text_uri,
                "hash": document.hash,
                "parse_status": document.parse_status,
            }

            # Create or update
            model, created = TrendDocumentModel.objects.update_or_create(
                id=document.id,
                defaults=model_data,
            )

            logger.info(f"Saved TrendDocument: {model.id} (created: {created})")

            # Convert back to entity
            return self._model_to_entity(model)

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            raise RuntimeError("Django models not available") from e

    async def get_by_id(self, document_id: UUID) -> TrendDocument | None:
        """Get document by ID.

        Args:
            document_id: Document UUID

        Returns:
            TrendDocument entity or None
        """
        try:
            from apps.trend_knowledge.models import TrendDocument as TrendDocumentModel

            model = TrendDocumentModel.objects.filter(id=document_id).first()
            if model:
                return self._model_to_entity(model)
            return None

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return None

    async def list_by_source(
        self,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TrendDocument]:
        """List documents by source ID.

        Args:
            source_id: Source UUID
            limit: Maximum results
            offset: Query offset

        Returns:
            List of TrendDocument entities
        """
        try:
            from apps.trend_knowledge.models import TrendDocument as TrendDocumentModel

            models = TrendDocumentModel.objects.filter(
                source_id=source_id,
            )[offset:offset + limit]

            return [self._model_to_entity(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    async def list_failed(self, limit: int = 50) -> list[TrendDocument]:
        """List failed documents for retry.

        Args:
            limit: Maximum results

        Returns:
            List of failed TrendDocument entities
        """
        try:
            from apps.trend_knowledge.models import TrendDocument as TrendDocumentModel

            models = TrendDocumentModel.objects.filter(
                parse_status=TrendDocumentStatus.FAILED.value,
            )[:limit]

            return [self._model_to_entity(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    async def find_by_hash(self, content_hash: str) -> TrendDocument | None:
        """Find document by content hash for deduplication.

        Args:
            content_hash: SHA256 hash of document content

        Returns:
            TrendDocument entity or None
        """
        try:
            from apps.trend_knowledge.models import TrendDocument as TrendDocumentModel

            model = TrendDocumentModel.objects.filter(
                hash=content_hash,
            ).first()

            if model:
                return self._model_to_entity(model)
            return None

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return None

    def _model_to_entity(self, model: Any) -> TrendDocument:
        """Convert Django model to domain entity.

        Args:
            model: Django TrendDocument model

        Returns:
            TrendDocument domain entity
        """
        return TrendDocument(
            id=model.id,
            source_id=model.source_id,
            title=model.title,
            url=model.url,
            published_at=model.published_at,
            collected_at=model.collected_at,
            raw_uri=model.raw_uri,
            parsed_text_uri=model.parsed_text_uri,
            hash=model.hash,
            parse_status=model.parse_status,
        )
