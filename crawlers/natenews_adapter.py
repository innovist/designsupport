"""
네이트뉴스 크롤러 어댑터
BaseCrawler 인터페이스에 맞게 기존 NateNewsCrawler를 래핑

지원 기능:
- 키워드 검색 크롤링
- 기간 설정 (start_date, end_date)
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base_crawler import BaseCrawler, CrawledItem

logger = logging.getLogger(__name__)


class NateNewsAdapter(BaseCrawler):
    """NateNewsCrawler를 BaseCrawler 인터페이스로 래핑"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._crawler = None
        self._initialized = False

    def _ensure_crawler(self):
        """크롤러 지연 초기화"""
        if self._initialized:
            return self._crawler is not None

        self._initialized = True
        try:
            from .nate_news_crawler import NateNewsCrawler
            self._crawler = NateNewsCrawler()
            logger.info("네이트뉴스 크롤러 초기화 성공")
            return True
        except Exception as e:
            logger.warning(f"네이트뉴스 크롤러 초기화 실패: {e}")
            self._crawler = None
            return False

    def get_channel_name(self) -> str:
        return "NateNews"

    async def crawl(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        """
        네이트뉴스 크롤링 실행

        Args:
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일

        Returns:
            CrawledItem 목록
        """
        if not self._ensure_crawler():
            logger.warning("네이트뉴스 크롤러 사용 불가")
            return []

        items = []

        try:
            # 날짜 형식 변환
            start_str = start_date.strftime("%Y-%m-%d") if start_date else ""
            end_str = end_date.strftime("%Y-%m-%d") if end_date else ""

            # 동기 함수를 스레드풀에서 실행
            loop = asyncio.get_event_loop()
            post_data, comment_data = await loop.run_in_executor(
                None,
                lambda: self._crawler.run(keyword, self.max_items, start_str, end_str)
            )

            # post_data를 CrawledItem으로 변환
            for post in post_data:
                if not post:
                    continue

                post_id = post.get("id", "")
                post_comments = [c for c in comment_data if c.get("blog_id") == post_id]

                item = CrawledItem(
                    title=post.get("title", ""),
                    content=post.get("content", ""),
                    url=post.get("link", ""),
                    author=post.get("user_id", ""),
                    date=self._parse_date(post.get("published_date")),
                    views=post.get("view_count") or 0,
                    likes=post.get("like_count") or 0,
                    comments=len(post_comments),
                    platform="natenews",
                    source_id=post_id,
                    metadata={
                        "comments": post_comments
                    }
                )
                item.quality_score = self.calculate_quality_score(item)
                items.append(item)

            logger.info(f"네이트뉴스 크롤링 완료: {len(items)}개 수집")

        except Exception as e:
            logger.error(f"네이트뉴스 크롤링 오류: {e}")

        return items

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str or date_str == "날짜 없음":
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return None
