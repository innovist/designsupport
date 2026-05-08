"""Django ORM repository for ParsingFailureQueue entities.

Implements ParsingFailureQueueRepositoryPort using Django models.
"""
from logging import getLogger
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import ParsingFailureQueueRepositoryPort
from apps.trend_knowledge.domain.entities import ParsingFailureQueue

logger = getLogger(__name__)


class DjangoParsingFailureQueueRepository(ParsingFailureQueueRepositoryPort):
    """Django ORM repository for ParsingFailureQueue.

    Tracks failed documents for admin review and retry.
    """

    async def save(self, failure: ParsingFailureQueue) -> ParsingFailureQueue:
        """Save a failure queue entry.

        Args:
            failure: ParsingFailureQueue entity to save

        Returns:
            Saved ParsingFailureQueue entity

        Raises:
            RuntimeError: If Django models not available
        """
        try:
            from apps.trend_knowledge.infrastructure.orm.models import (
                ParsingFailureQueue as ParsingFailureQueueModel,
            )

            # Convert entity to model
            model_data = {
                "id": failure.id,
                "document_id": failure.document_id,
                "reason": failure.reason,
                "retried_count": failure.retried_count,
                "created_at": failure.created_at,
            }

            # Create or update
            model, created = ParsingFailureQueueModel.objects.update_or_create(
                document_id=failure.document_id,
                defaults=model_data,
            )

            logger.info(f"Saved ParsingFailureQueue: {model.id} (created: {created})")

            # Convert back to entity
            return self._model_to_entity(model)

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            raise RuntimeError("Django models not available") from e

    async def list_pending(
        self,
        limit: int = 50,
    ) -> list[ParsingFailureQueue]:
        """List pending failures for retry.

        Args:
            limit: Maximum results

        Returns:
            List of ParsingFailureQueue entities
        """
        try:
            from apps.trend_knowledge.infrastructure.orm.models import (
                ParsingFailureQueue as ParsingFailureQueueModel,
            )

            # Order by creation date (newest first)
            models = ParsingFailureQueueModel.objects.all().order_by("-created_at")[:limit]
            return [self._model_to_entity(m) for m in models]

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            return []

    async def delete(self, failure_id: UUID) -> None:
        """Delete a failure queue entry.

        Args:
            failure_id: Failure UUID to delete

        Raises:
            RuntimeError: If Django models not available
        """
        try:
            from apps.trend_knowledge.infrastructure.orm.models import (
                ParsingFailureQueue as ParsingFailureQueueModel,
            )

            model = ParsingFailureQueueModel.objects.filter(id=failure_id).first()
            if model:
                model.delete()
                logger.info(f"Deleted ParsingFailureQueue: {failure_id}")
            else:
                logger.warning(f"ParsingFailureQueue not found: {failure_id}")

        except ImportError as e:
            logger.error(f"Django models not available: {e}")
            raise RuntimeError("Django models not available") from e

    def _model_to_entity(self, model: Any) -> ParsingFailureQueue:
        """Convert Django model to domain entity.

        Args:
            model: Django ParsingFailureQueue model

        Returns:
            ParsingFailureQueue domain entity
        """
        return ParsingFailureQueue(
            id=model.id,
            document_id=model.document_id,
            reason=model.reason,
            created_at=model.created_at,
            retried_count=model.retried_count,
        )
