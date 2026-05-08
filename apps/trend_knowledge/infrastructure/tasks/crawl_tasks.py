"""Celery tasks for trend crawling operations.

Scheduled crawling of active trend sources.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from celery import shared_task
from celery.utils.log import get_task_logger

from apps.trend_knowledge.application.use_cases.crawl_source import (
    CrawlSourceUseCase,
)
from apps.trend_knowledge.domain.entities import TrendSource
from apps.trend_knowledge.infrastructure.repositories import (
    DjangoTrendSourceRepository,
)

logger = get_task_logger(__name__)


@shared_task(
    name="trend_knowledge.crawl_source",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def crawl_source_task(self, source_id: str) -> str:
    """Crawl a single trend source.

    Args:
        source_id: Source UUID as string

    Returns:
        Result message

    Raises:
        Exception: If crawling fails after retries
    """
    try:
        source_uuid = UUID(source_id)

        # Get source from repository
        source_repo = DjangoTrendSourceRepository()
        source = source_repo.get_by_id(source_uuid)

        if source is None:
            logger.error(f"Source not found: {source_id}")
            return f"Source not found: {source_id}"

        if not source.active:
            logger.warning(f"Source is inactive: {source_id}")
            return f"Source is inactive: {source_id}"

        # Execute crawl use case
        use_case = CrawlSourceUseCase(
            crawler=None,  # Would be injected via DI
            document_repo=None,  # Would be injected via DI
            source_repo=source_repo,
        )

        result = use_case.execute(source)

        logger.info(f"Crawled source {source_id}: {result.documents_collected} documents")
        return f"Crawled {result.documents_collected} documents from {source_id}"

    except Exception as e:
        logger.error(f"Crawl task failed for source {source_id}: {e}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)

        return f"Failed after {self.request.retries} retries: {e}"


@shared_task(
    name="trend_knowledge.crawl_active_sources",
    bind=True,
)
def crawl_active_sources_task(self) -> str:
    """Crawl all active trend sources.

    Scheduled task (beat schedule) for periodic crawling.
    Only crawls sources where current time matches their cron schedule.

    Returns:
        Result message with statistics
    """
    try:
        # Get all active sources
        source_repo = DjangoTrendSourceRepository()
        sources = source_repo.list_active()

        if not sources:
            logger.info("No active sources to crawl")
            return "No active sources to crawl"

        # Filter sources by crawl schedule
        # This is simplified - real implementation would check cron schedule
        now = datetime.now(timezone.utc)
        sources_to_crawl = [s for s in sources if _should_crawl_now(s, now)]

        if not sources_to_crawl:
            logger.info(f"No sources due for crawling at {now}")
            return f"No sources due for crawling at {now}"

        # Queue crawl tasks for each source
        for source in sources_to_crawl:
            crawl_source_task.delay(str(source.id))

        logger.info(f"Queued {len(sources_to_crawl)} sources for crawling")
        return f"Queued {len(sources_to_crawl)} sources for crawling"

    except Exception as e:
        logger.error(f"Crawl active sources task failed: {e}")
        return f"Failed: {e}"


def _should_crawl_now(source: TrendSource, now: datetime) -> bool:
    """Check if source should be crawled now based on schedule.

    Args:
        source: TrendSource to check
        now: Current timestamp

    Returns:
        True if should crawl, False otherwise

    Note:
        This is a simplified implementation.
        Full implementation would parse cron expression and check if current time matches.
    """
    # Simplified: crawl all active sources
    # Real implementation would use croniter to parse crawl_schedule
    return True
