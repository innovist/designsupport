"""Celery tasks for insight extraction operations.

Extracts insights from parsed documents using AI models.
"""
import logging
from uuid import UUID

from celery import shared_task
from celery.utils.log import get_task_logger

from apps.trend_knowledge.application.use_cases.extract_insights import (
    ExtractInsightsUseCase,
)
from apps.trend_knowledge.domain.services import (
    InsightConfidenceCalculator,
    RecencyScoreCalculator,
)
from apps.trend_knowledge.infrastructure.repositories import (
    DjangoTrendDocumentRepository,
    DjangoTrendInsightRepository,
)

logger = get_task_logger(__name__)


@shared_task(
    name="trend_knowledge.extract_insights",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def extract_insights_task(self, document_id: str) -> str:
    """Extract insights from a parsed document.

    Args:
        document_id: Document UUID as string

    Returns:
        Result message

    Raises:
        Exception: If extraction fails after retries
    """
    try:
        document_uuid = UUID(document_id)

        # Get document from repository
        document_repo = DjangoTrendDocumentRepository()
        document = document_repo.get_by_id(document_uuid)

        if document is None:
            logger.error(f"Document not found: {document_id}")
            return f"Document not found: {document_id}"

        # Check if document is parsed
        if document.parse_status != "parsed":
            logger.warning(f"Document {document_id} not parsed yet")
            return f"Document {document_id} not parsed yet"

        # Execute extract insights use case
        insight_repo = DjangoTrendInsightRepository()
        model_port = None  # Would be injected via DI (delegates to ModelRouter)

        confidence_calculator = InsightConfidenceCalculator()
        recency_calculator = RecencyScoreCalculator()

        use_case = ExtractInsightsUseCase(
            model_port=model_port,
            insight_repo=insight_repo,
            document_repo=document_repo,
            confidence_calculator=confidence_calculator,
            recency_calculator=recency_calculator,
        )

        result = use_case.execute(document)

        logger.info(
            f"Extracted {result.insights_count} insights from document {document_id}"
        )
        return f"Extracted {result.insights_count} insights from document {document_id}"

    except Exception as e:
        logger.error(f"Extract insights task failed for document {document_id}: {e}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries * 30)

        return f"Failed after {self.request.retries} retries: {e}"
