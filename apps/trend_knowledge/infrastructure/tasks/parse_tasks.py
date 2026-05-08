"""Celery tasks for document parsing operations.

Parses raw documents and retries failed documents.
"""
import logging
from uuid import UUID

from celery import shared_task
from celery.utils.log import get_task_logger

from apps.trend_knowledge.application.use_cases.parse_document import (
    ParseDocumentUseCase,
)
from asgiref.sync import async_to_sync

from apps.trend_knowledge.infrastructure.adapters.parsers import get_parser_registry
from apps.trend_knowledge.infrastructure.repositories import (
    DjangoTrendDocumentRepository,
    DjangoParsingFailureQueueRepository,
)

logger = get_task_logger(__name__)


@shared_task(
    name="trend_knowledge.parse_document",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
)
def parse_document_task(self, document_id: str) -> str:
    """Parse a single document.

    Args:
        document_id: Document UUID as string

    Returns:
        Result message

    Raises:
        Exception: If parsing fails after retries
    """
    try:
        document_uuid = UUID(document_id)

        document_repo = DjangoTrendDocumentRepository()
        parser = get_parser_registry()
        failure_repo = DjangoParsingFailureQueueRepository()

        use_case = ParseDocumentUseCase(
            document_repository=document_repo,
            parser_port=parser,
            failure_queue_repository=failure_repo,
        )

        result = async_to_sync(use_case.execute)(document_uuid)

        logger.info("Parsed document %s: %s", document_id, result)
        return f"Parsed document {document_id}: {result.get('status')}"

    except Exception as e:
        logger.error(f"Parse task failed for document {document_id}: {e}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries * 30)

        return f"Failed after {self.request.retries} retries: {e}"


@shared_task(
    name="trend_knowledge.retry_failed_parses",
    bind=True,
)
def retry_failed_parses_task(self) -> str:
    """Retry failed documents from parsing failure queue.

    Returns:
        Result message with statistics

    Note:
        This task would be scheduled periodically to retry failed documents.
    """
    try:
        # Get failed documents from queue
        failure_repo = DjangoParsingFailureQueueRepository()
        failures = async_to_sync(failure_repo.list_pending)(limit=50)

        if not failures:
            logger.info("No failed documents to retry")
            return "No failed documents to retry"

        # Queue parse tasks for each failed document
        retried_count = 0
        for failure in failures:
            # Skip if already retried too many times
            if failure.retried_count >= 3:
                logger.warning(f"Document {failure.document_id} exceeded retry limit")
                continue

            # Increment retry count
            failure.increment_retry()
            async_to_sync(failure_repo.save)(failure)

            # Queue parse task
            parse_document_task.delay(str(failure.document_id))
            retried_count += 1

        logger.info(f"Queued {retried_count} failed documents for retry")
        return f"Queued {retried_count} failed documents for retry"

    except Exception as e:
        logger.error(f"Retry failed parses task failed: {e}")
        return f"Failed: {e}"
