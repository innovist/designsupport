"""
Crawler service for orchestrating multiple crawlers
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from enum import Enum

from app.core.config import get_settings
from .base_crawler import BaseCrawler, CrawledItem
from .fashion_news_crawler import FashionNewsCrawler
from .fashion_insta_crawler import FashionInstaCrawler
from .musinsa_crawler import MusinsaCrawler
from .wgsn_crawler import WGSNCrawler
from .pinterest_crawler import PinterestCrawler
from .youtube_adapter import YouTubeAdapter
from .natenews_adapter import NateNewsAdapter

logger = logging.getLogger(__name__)
YOUTUBE_TIMEOUT_MIN_SECONDS = 300
NATENEWS_TIMEOUT_MIN_SECONDS = 60


class CrawlStatus(Enum):
    """크롤링 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlProgress:
    """크롤링 진행 상황"""

    def __init__(self):
        self.total_items = 0
        self.completed_items = 0
        self.failed_items = 0
        self.current_crawler = ""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status = CrawlStatus.PENDING
        self.error_message: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        """진행률 퍼센트"""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100

    @property
    def elapsed_time(self) -> Optional[float]:
        """경과 시간 (초)"""
        if not self.start_time:
            return None
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()


class CrawlerCancellationToken:
    """크롤링 취소 토큰"""

    def __init__(self):
        self._cancelled = False
        self._reason: Optional[str] = None

    def cancel(self, reason: str = "User cancelled"):
        """취소 요청"""
        self._cancelled = True
        self._reason = reason
        logger.info(f"Crawling cancelled: {reason}")

    @property
    def is_cancelled(self) -> bool:
        """취소 여부"""
        return self._cancelled

    @property
    def reason(self) -> Optional[str]:
        """취소 사유"""
        return self._reason

    def check_cancelled(self):
        """취소 확인 (예외 발생)"""
        if self._cancelled:
            raise CrawlerCancelledException(self._reason or "Crawling was cancelled")


class CrawlerCancelledException(Exception):
    """크롤링 취소 예외"""
    pass


class CrawlerErrorHandler:
    """크롤러 에러 핸들러"""

    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.max_retries = 3
        self.retry_delay = 1.0

    def handle_error(self, crawler_name: str, error: Exception) -> bool:
        """
        에러 처리

        Args:
            crawler_name: 크롤러 이름
            error: 발생한 에러

        Returns:
            재시도 여부
        """
        self.error_counts[crawler_name] = self.error_counts.get(crawler_name, 0) + 1

        if self.error_counts[crawler_name] >= self.max_retries:
            logger.error(f"Max retries exceeded for {crawler_name}: {error}")
            return False

        logger.warning(f"Error in {crawler_name} (attempt {self.error_counts[crawler_name]}): {error}")
        return True

    def should_retry(self, crawler_name: str) -> bool:
        """재시도 여부 확인"""
        return self.error_counts.get(crawler_name, 0) < self.max_retries


class ProgressCallback:
    """진행률 콜백"""

    def __init__(self, callback: Optional[Callable[[CrawlProgress], None]] = None):
        self.callback = callback

    def update(self, progress: CrawlProgress):
        """진행률 업데이트"""
        if self.callback:
            self.callback(progress)

        # 로그 출력
        logger.info(
            f"Crawling progress: {progress.progress_percent:.1f}% "
            f"({progress.completed_items}/{progress.total_items}) "
            f"- {progress.current_crawler}"
        )


class CrawlerService:
    """크롤러 서비스"""
    # @MX:ANCHOR: [AUTO] Central orchestrator for all crawler operations. Manages crawler registration, execution, and job lifecycle.
    # @MX:REASON: High fan_in component called by GUI, API endpoints, and background jobs. Changes affect all crawler consumers.

    def __init__(self, max_workers: int = 5, timeout_seconds: Optional[int] = None):
        """
        초기화

        Args:
            max_workers: 최대 동시 작업자 수
            timeout_seconds: 크롤러 타임아웃(초)
        """
        settings = get_settings()
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else settings.crawler_timeout_seconds
        self.crawlers: Dict[str, BaseCrawler] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._register_default_crawlers()

        # 작업 관리용 저장소
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._job_counter = 0
        self._cancel_tokens: Dict[str, CrawlerCancellationToken] = {}
        self._last_errors: Dict[str, str] = {}

    def _register_default_crawlers(self):
        """기본 크롤러 등록"""
        self.register_crawler("fashion_news", FashionNewsCrawler())
        self.register_crawler("fashion_insta", FashionInstaCrawler())
        self.register_crawler("musinsa", MusinsaCrawler())
        self.register_crawler("wgsn", WGSNCrawler())
        self.register_crawler("pinterest", PinterestCrawler())

        # 유튜브 및 뉴스 크롤러 (어댑터)
        self.register_crawler("youtube", YouTubeAdapter())
        self.register_crawler("natenews", NateNewsAdapter())

    def register_crawler(self, name: str, crawler: BaseCrawler):
        """
        크롤러 등록

        Args:
            name: 크롤러 이름
            crawler: 크롤러 인스턴스
        """
        self.crawlers[name] = crawler
        logger.info(f"Registered crawler: {name}")

    def get_available_crawlers(self) -> List[str]:
        """사용 가능한 크롤러 목록 반환"""
        return list(self.crawlers.keys())

    def _resolve_crawlers(self, enabled_crawlers: Optional[List[str]]) -> Dict[str, BaseCrawler]:
        if enabled_crawlers:
            return {
                name: self.crawlers[name]
                for name in enabled_crawlers
                if name in self.crawlers
            }
        return self.crawlers

    async def _gather_crawler_tasks(
        self,
        crawlers_to_run: Dict[str, BaseCrawler],
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        progress: CrawlProgress,
        error_handler: CrawlerErrorHandler,
        cancel_token: Optional[CrawlerCancellationToken]
    ) -> List[Any]:
        tasks = [
            asyncio.create_task(
                self._run_single_crawler(
                    name,
                    crawler,
                    keyword,
                    start_date,
                    end_date,
                    progress,
                    error_handler,
                    cancel_token
                )
            )
            for name, crawler in crawlers_to_run.items()
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _merge_crawler_results(self, results: List[Any]) -> List[CrawledItem]:
        all_items: List[CrawledItem] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Crawler task failed: {result}")
            elif isinstance(result, list):
                all_items.extend(result)
        return all_items

    def _init_progress(self, total_items: int) -> CrawlProgress:
        progress = CrawlProgress()
        progress.status = CrawlStatus.RUNNING
        progress.start_time = datetime.utcnow()
        progress.total_items = total_items
        return progress

    async def _execute_crawl_tasks(
        self,
        crawlers_to_run: Dict[str, BaseCrawler],
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        progress: CrawlProgress,
        error_handler: CrawlerErrorHandler,
        cancel_token: Optional[CrawlerCancellationToken]
    ) -> List[CrawledItem]:
        try:
            results = await self._gather_crawler_tasks(
                crawlers_to_run,
                keyword,
                start_date,
                end_date,
                progress,
                error_handler,
                cancel_token
            )
            return self._merge_crawler_results(results)
        except CrawlerCancelledException:
            progress.status = CrawlStatus.CANCELLED
            progress.error_message = "Cancelled by user"
            logger.info("Crawling cancelled")
        except Exception as e:
            progress.status = CrawlStatus.FAILED
            progress.error_message = str(e)
            logger.error(f"Crawling failed: {e}")
        return []

    def _finalize_progress(self, progress: CrawlProgress, progress_callback: Optional[ProgressCallback]) -> None:
        progress.end_time = datetime.utcnow()
        if progress.status == CrawlStatus.RUNNING:
            progress.status = CrawlStatus.COMPLETED
        if progress_callback:
            progress_callback.update(progress)

    async def crawl_all(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        enabled_crawlers: Optional[List[str]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        cancel_token: Optional[CrawlerCancellationToken] = None
    ) -> List[CrawledItem]:
        """
        모든 크롤러로 크롤링 실행

        Args:
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일
            enabled_crawlers: 활성화할 크롤러 목록
            progress_callback: 진행률 콜백
            cancel_token: 취소 토큰

        Returns:
            수집된 데이터 목록
        """
        # @MX:WARN: [AUTO] Complex async orchestration with parallel task execution, error handling, and cancellation support.
        # @MX:REASON: Manages multiple concurrent crawler tasks with asyncio.gather(), error aggregation, and progress tracking. Complexity from error recovery and timeout handling.
        # 활성화할 크롤러 결정
        crawlers_to_run = self._resolve_crawlers(enabled_crawlers)

        if not crawlers_to_run:
            logger.warning("No crawlers to run")
            return []

        self._reset_last_errors()
        progress = self._init_progress(len(crawlers_to_run))
        error_handler = CrawlerErrorHandler()
        all_items = await self._execute_crawl_tasks(
            crawlers_to_run,
            keyword,
            start_date,
            end_date,
            progress,
            error_handler,
            cancel_token
        )
        self._finalize_progress(progress, progress_callback)

        # 중복 제거
        unique_items = self._remove_duplicate_items(all_items)
        logger.info(f"Collected {len(unique_items)} unique items from {len(crawlers_to_run)} crawlers")

        return unique_items

    def _reset_last_errors(self) -> None:
        self._last_errors = {}

    def _record_error(self, crawler_name: str, error: Exception) -> None:
        self._last_errors[crawler_name] = str(error)

    def get_last_errors(self) -> Dict[str, str]:
        return dict(self._last_errors)

    def _resolve_timeout(self, crawler_name: str) -> int:
        try:
            timeout = int(self.timeout_seconds or 0)
        except (TypeError, ValueError):
            timeout = 0
        if crawler_name == "youtube":
            return max(timeout, YOUTUBE_TIMEOUT_MIN_SECONDS)
        if crawler_name == "natenews":
            return max(timeout, NATENEWS_TIMEOUT_MIN_SECONDS)
        return timeout

    async def _run_with_timeout(self, crawler_name: str, phase: str, coro, timeout: Optional[int] = None):
        timeout = timeout if timeout is not None else self.timeout_seconds
        if not timeout or timeout <= 0:
            return await coro
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"{crawler_name} {phase} timeout ({timeout}s)") from exc

    async def _execute_crawler(
        self,
        name: str,
        crawler: BaseCrawler,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        timeout = self._resolve_timeout(name)
        items = await self._run_with_timeout(
            name,
            "crawl",
            crawler.crawl(keyword, start_date, end_date),
            timeout
        )
        return await self._run_with_timeout(
            name,
            "post_process",
            crawler.post_process_items(items),
            timeout
        )

    def _fail_crawler(self, name: str, progress: CrawlProgress, error: Exception, label: str) -> None:
        progress.failed_items += 1
        self._record_error(name, error)
        logger.error(f"Crawler {name} {label}: {error}")

    async def _run_single_crawler(
        self,
        name: str,
        crawler: BaseCrawler,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        progress: CrawlProgress,
        error_handler: CrawlerErrorHandler,
        cancel_token: Optional[CrawlerCancellationToken]
    ) -> List[CrawledItem]:
        """단일 크롤러 실행"""
        progress.current_crawler = name
        try:
            if cancel_token:
                cancel_token.check_cancelled()
            if self.max_workers > 1:
                await asyncio.sleep(0.5)
            processed_items = await self._execute_crawler(
                name,
                crawler,
                keyword,
                start_date,
                end_date
            )
            progress.completed_items += 1
            logger.info(f"Crawler {name} completed: {len(processed_items)} items")
            return processed_items
        except CrawlerCancelledException:
            raise
        except Exception as e:
            if isinstance(e, TimeoutError):
                self._fail_crawler(name, progress, e, "timeout")
                return []
            if error_handler.handle_error(name, e) and error_handler.should_retry(name):
                logger.info(f"Retrying crawler {name}...")
                await asyncio.sleep(error_handler.retry_delay)
                return await self._run_single_crawler(
                    name, crawler, keyword, start_date, end_date,
                    progress, error_handler, cancel_token
                )
            self._fail_crawler(name, progress, e, "failed")
            return []

    async def crawl_single(
        self,
        crawler_name: str,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        """
        단일 크롤러 실행

        Args:
            crawler_name: 크롤러 이름
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일

        Returns:
            수집된 데이터 목록
        """
        if crawler_name not in self.crawlers:
            raise ValueError(f"Crawler not found: {crawler_name}")

        crawler = self.crawlers[crawler_name]
        items = await crawler.crawl(keyword, start_date, end_date)
        return await crawler.post_process_items(items)

    def _remove_duplicate_items(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """중복 아이템 제거"""
        # @MX:NOTE: [AUTO] Deduplication using URL and source_id as primary keys. Preserves first occurrence of each unique item.
        seen_urls = set()
        seen_ids = set()
        unique_items = []

        for item in items:
            # URL 기준 중복 체크
            if item.url and item.url in seen_urls:
                continue
            if item.url:
                seen_urls.add(item.url)

            # ID 기준 중복 체크
            if item.source_id and item.source_id in seen_ids:
                continue
            if item.source_id:
                seen_ids.add(item.source_id)

            unique_items.append(item)

        return unique_items

    async def get_crawler_stats(self) -> Dict[str, Any]:
        """크롤러 통계 정보 반환"""
        stats = {
            "total_crawlers": len(self.crawlers),
            "available_crawlers": list(self.crawlers.keys()),
            "max_workers": self.max_workers
        }

        # 각 크롤러별 정보
        for name, crawler in self.crawlers.items():
            stats[f"crawler_{name}"] = {
                "channel_name": crawler.get_channel_name(),
                "supports_search": crawler.supports_search(),
                "supports_date_range": crawler.supports_date_range(),
                "config": crawler.config
            }

        return stats

    # ===== Job Management Methods =====

    async def start_crawl(
        self,
        keywords: List[str],
        sources: List[str],
        max_pages: int = 10,
        youtube_channel_urls: Optional[List[str]] = None
    ) -> str:
        """
        크롤링 작업 시작

        Args:
            keywords: 검색 키워드 목록
            sources: 크롤러 소스 목록
            max_pages: 최대 페이지 수
            youtube_channel_urls: 유튜브 채널 URL 목록

        Returns:
            작업 ID
        """
        # @MX:WARN: [AUTO] Creates background tasks without explicit task lifecycle management. Tasks may outlive the job context.
        # @MX:REASON: Uses asyncio.create_task() for background execution. Tasks are tracked in _jobs dict but not explicitly awaited or cancelled on shutdown.
        self._job_counter += 1
        job_id = f"crawl_{self._job_counter}_{int(time.time())}"

        # 취소 토큰 생성
        cancel_token = CrawlerCancellationToken()
        self._cancel_tokens[job_id] = cancel_token

        # 작업 정보 저장
        self._jobs[job_id] = {
            "id": job_id,
            "keywords": keywords,
            "sources": sources,
            "max_pages": max_pages,
            "youtube_channel_urls": youtube_channel_urls or [],
            "status": CrawlStatus.PENDING.value,
            "progress": 0,
            "items_collected": 0,
            "results": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None
        }

        # 백그라운드 태스크로 크롤링 실행
        asyncio.create_task(self._execute_crawl_job(job_id, keywords, sources, cancel_token, youtube_channel_urls))

        logger.info(f"Started crawl job: {job_id}")
        return job_id

    async def _execute_crawl_job(
        self,
        job_id: str,
        keywords: List[str],
        sources: List[str],
        cancel_token: CrawlerCancellationToken,
        youtube_channel_urls: Optional[List[str]] = None
    ):
        """크롤링 작업 실행"""
        # @MX:WARN: [AUTO] Long-running background task with complex state management. Mutates shared _jobs dict without lock.
        # @MX:REASON: Updates job state in _jobs dict from async context without explicit synchronization. Multiple concurrent jobs could race.
        job = self._jobs.get(job_id)
        if not job:
            return

        job["status"] = CrawlStatus.RUNNING.value

        # YouTube 크롤러에 채널 URL 설정
        if youtube_channel_urls and "youtube" in self.crawlers:
            youtube_crawler = self.crawlers["youtube"]
            if hasattr(youtube_crawler, "set_channel_urls"):
                youtube_crawler.set_channel_urls(youtube_channel_urls)
                logger.info(f"YouTube 채널 URL {len(youtube_channel_urls)}개 설정됨")

        try:
            all_results = []

            for keyword in keywords:
                if cancel_token.is_cancelled:
                    break

                # 진행률 콜백 설정
                def update_progress(progress: CrawlProgress):
                    if job_id in self._jobs:
                        self._jobs[job_id]["progress"] = progress.progress_percent
                        self._jobs[job_id]["items_collected"] = progress.completed_items

                progress_callback = ProgressCallback(update_progress)

                items = await self.crawl_all(
                    keyword=keyword,
                    enabled_crawlers=sources,
                    progress_callback=progress_callback,
                    cancel_token=cancel_token
                )

                # CrawledItem을 딕셔너리로 변환
                for item in items:
                    all_results.append({
                        "id": item.source_id,
                        "title": item.title,
                        "content": item.content,
                        "source": item.source,
                        "url": item.url,
                        "published_at": item.published_at.isoformat() if item.published_at else None,
                        "keywords": item.keywords,
                        "image_urls": item.image_urls,
                        "metadata": item.metadata
                    })

            job["results"] = all_results
            job["items_collected"] = len(all_results)
            job["status"] = CrawlStatus.COMPLETED.value
            job["progress"] = 100

        except CrawlerCancelledException:
            job["status"] = CrawlStatus.CANCELLED.value
            job["error"] = "Cancelled by user"

        except Exception as e:
            job["status"] = CrawlStatus.FAILED.value
            job["error"] = str(e)
            logger.error(f"Crawl job failed: {job_id}, error: {e}")

        finally:
            job["completed_at"] = datetime.utcnow().isoformat()
            if job_id in self._cancel_tokens:
                del self._cancel_tokens[job_id]

    async def get_crawl_status(self, job_id: str) -> Dict[str, Any]:
        """
        크롤링 작업 상태 조회

        Args:
            job_id: 작업 ID

        Returns:
            작업 상태 정보
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        return {
            "job_id": job["id"],
            "status": job["status"],
            "progress": job["progress"],
            "items_collected": job["items_collected"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
            "error": job["error"]
        }

    async def get_crawl_results(self, job_id: str) -> List[Dict[str, Any]]:
        """
        크롤링 결과 조회

        Args:
            job_id: 작업 ID

        Returns:
            수집된 데이터 목록
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        return job.get("results", [])

    async def cancel_crawl(self, job_id: str):
        """
        크롤링 작업 취소

        Args:
            job_id: 작업 ID
        """
        cancel_token = self._cancel_tokens.get(job_id)
        if cancel_token:
            cancel_token.cancel("User cancelled")
            logger.info(f"Cancelled crawl job: {job_id}")
        else:
            raise ValueError(f"Job not found or already completed: {job_id}")

    def __del__(self):
        """소멸자"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
