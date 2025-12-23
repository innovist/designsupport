"""
YouTube 크롤러 어댑터
BaseCrawler 인터페이스에 맞게 기존 YoutubeCrawler를 래핑

지원 기능:
- 키워드 검색 크롤링 (run)
- 채널 URL 기반 크롤링 (run_channel)
- 병렬 수집 (max_workers 설정)
- 기간 설정 (start_date, end_date)
- STT 음성 전사 (선택)
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base_crawler import BaseCrawler, CrawledItem

logger = logging.getLogger(__name__)


class YouTubeAdapter(BaseCrawler):
    """YoutubeCrawler를 BaseCrawler 인터페이스로 래핑"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._crawler = None
        self._initialized = False

        # 설정 옵션
        self.enable_stt = config.get("enable_stt") if config else None
        self.max_workers = config.get("max_workers", 3) if config else 3
        self.channel_urls = config.get("channel_urls", []) if config else []
        self.keyword_max_items = config.get("keyword_max_items") if config else None
        self.channel_max_items = config.get("channel_max_items") if config else None

    def set_channel_urls(self, urls: List[str]):
        """런타임에 채널 URL 설정"""
        self.channel_urls = urls or []
        logger.debug(f"YouTube 채널 URL 설정: {len(self.channel_urls)}개")

    def apply_config(
        self,
        enable_stt: Optional[bool] = None,
        max_workers: Optional[int] = None,
        channel_urls: Optional[List[str]] = None,
        keyword_max_items: Optional[int] = None,
        channel_max_items: Optional[int] = None,
        max_items: Optional[int] = None
    ) -> None:
        reset_needed = False
        if enable_stt is not None and enable_stt != self.enable_stt:
            self.enable_stt = enable_stt
            reset_needed = True
        if max_workers is not None:
            try:
                max_workers = int(max_workers)
            except (TypeError, ValueError):
                max_workers = None
        if max_workers is not None and max_workers > 0 and max_workers != self.max_workers:
            self.max_workers = max_workers
            reset_needed = True
        if max_items is not None:
            self.max_items = max(1, int(max_items))
        if channel_urls is not None:
            self.channel_urls = channel_urls or []
        if keyword_max_items is not None:
            try:
                self.keyword_max_items = max(1, int(keyword_max_items))
            except (TypeError, ValueError):
                self.keyword_max_items = None
        if channel_max_items is not None:
            try:
                self.channel_max_items = max(1, int(channel_max_items))
            except (TypeError, ValueError):
                self.channel_max_items = None
        if reset_needed:
            self._initialized = False
            self._crawler = None

    def _ensure_crawler(self):
        """크롤러 지연 초기화 (API 키 필요)"""
        if self._initialized:
            return self._crawler is not None

        self._initialized = True
        try:
            from .youtube_crawler import YoutubeCrawler
            self._crawler = YoutubeCrawler(
                enable_stt=self.enable_stt,
                max_workers=self.max_workers
            )
            logger.info(f"YouTube 크롤러 초기화 성공 (STT: {self.enable_stt}, workers: {self.max_workers})")
            return True
        except Exception as e:
            logger.warning(f"YouTube 크롤러 초기화 실패: {e}")
            self._crawler = None
            return False

    def get_channel_name(self) -> str:
        return "YouTube"

    async def crawl(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        """
        YouTube 크롤링 실행 (키워드 검색 + 채널 크롤링)

        Args:
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일

        Returns:
            CrawledItem 목록
        """
        if not self._ensure_crawler():
            logger.warning("YouTube 크롤러 사용 불가 - YOUTUBE_API_KEYS 환경변수 확인 필요")
            return []

        items = []
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None

        try:
            loop = asyncio.get_event_loop()

            # 1. 키워드 기반 검색 크롤링
            logger.info(f"YouTube 키워드 검색 크롤링: '{keyword}'")
            keyword_limit = self.keyword_max_items or self.max_items
            post_data, comment_data = await loop.run_in_executor(
                None,
                lambda: self._crawler.run(keyword, keyword_limit, start_str, end_str)
            )
            items.extend(self._convert_to_crawled_items(post_data, comment_data))

            # 2. 채널 URL 기반 크롤링 (설정된 경우)
            if self.channel_urls:
                channel_limit = self.channel_max_items
                if channel_limit is None:
                    channel_limit = max(1, self.max_items // len(self.channel_urls))
                for channel_url in self.channel_urls:
                    logger.info(f"YouTube 채널 크롤링: {channel_url}")
                    try:
                        ch_posts, ch_comments = await loop.run_in_executor(
                            None,
                            lambda url=channel_url: self._crawler.run_channel(
                                url, start_str, end_str, channel_limit
                            )
                        )
                        items.extend(self._convert_to_crawled_items(ch_posts, ch_comments))
                    except Exception as ch_err:
                        logger.error(f"채널 크롤링 오류 ({channel_url}): {ch_err}")

            logger.info(f"YouTube 크롤링 완료: {len(items)}개 수집")

        except Exception as e:
            logger.error(f"YouTube 크롤링 오류: {e}")

        return items

    def _convert_to_crawled_items(
        self,
        post_data: List[Dict],
        comment_data: List[Dict]
    ) -> List[CrawledItem]:
        """post_data를 CrawledItem 목록으로 변환"""
        items = []
        for post in post_data:
            if not post:
                continue

            post_id = post.get("id", "")
            post_comments = [c for c in comment_data if c.get("blog_id") == post_id]

            item = CrawledItem(
                title=post.get("title", ""),
                content=(post.get("content") or post.get("title") or ""),
                url=post.get("link", ""),
                author=post.get("user_id", ""),
                date=self._parse_date(post.get("published_date")),
                views=post.get("view_count") or 0,
                likes=post.get("like_count") or 0,
                comments=len(post_comments),
                platform="youtube",
                source_id=post_id,
                metadata={
                    "stt_success": post.get("stt_success", False),
                    "comments": post_comments
                }
            )
            item.quality_score = self.calculate_quality_score(item)
            items.append(item)
        return items

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return None
