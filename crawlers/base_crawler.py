"""
Base crawler for fashion data collection
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from .crawler_text_utils import (
    clean_text,
    extract_fashion_keywords,
    extract_product_links,
    extract_image_urls
)

logger = logging.getLogger(__name__)

DEFAULT_MIN_CONTENT_LENGTH = 50
YOUTUBE_MIN_CONTENT_LENGTH = 20


@dataclass
class CrawledItem:
    """표준화된 크롤링 데이터 포맷"""
    # 기본 정보
    title: str = ""
    content: str = ""
    url: str = ""

    # 메타데이터
    author: str = ""
    date: Optional[datetime] = None
    views: int = 0
    likes: int = 0
    comments: int = 0

    # 플랫폼 정보
    platform: str = ""
    source_id: str = ""  # 플랫폼별 고유 ID

    # 추가 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 품질 평가
    quality_score: float = 0.0
    relevance_score: float = 0.0

    # 패션 관련 정보
    fashion_tags: List[str] = field(default_factory=list)
    product_links: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)

    # 수집 정보
    crawled_at: datetime = field(default_factory=datetime.utcnow)
    crawl_session_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "author": self.author,
            "date": self.date.isoformat() if self.date else None,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "platform": self.platform,
            "source_id": self.source_id,
            "metadata": self.metadata,
            "quality_score": self.quality_score,
            "relevance_score": self.relevance_score,
            "fashion_tags": self.fashion_tags,
            "product_links": self.product_links,
            "image_urls": self.image_urls,
            "crawled_at": self.crawled_at.isoformat(),
            "crawl_session_id": self.crawl_session_id
        }

    @property
    def source(self) -> str:
        return self.platform

    @property
    def published_at(self) -> Optional[datetime]:
        return self.date

    @property
    def keywords(self) -> List[str]:
        return self.fashion_tags


class BaseCrawler(ABC):
    """크롤러 기본 클래스"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        초기화

        Args:
            config: 크롤러 설정
        """
        self.config = config or {}
        self.session_id = self.config.get("session_id", "")
        self.max_items = self.config.get("max_items", 100)
        self.delay = self.config.get("delay", 1)

    @abstractmethod
    async def crawl(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        """
        크롤링 실행 (추상 메서드)

        Args:
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일

        Returns:
            수집된 데이터 목록
        """
        pass

    @abstractmethod
    def get_channel_name(self) -> str:
        """채널/플랫폼 이름 반환"""
        pass

    def supports_search(self) -> bool:
        """검색 기능 지원 여부"""
        return True

    def supports_date_range(self) -> bool:
        """날짜 범위 필터링 지원 여부"""
        return True

    def calculate_quality_score(self, item: CrawledItem) -> float:
        """
        콘텐츠 품질 점수 계산 (0.0 - 1.0)

        Args:
            item: 평가할 아이템

        Returns:
            품질 점수
        """
        score = 0.0

        # 제목이 있음 (20점)
        if item.title and len(item.title.strip()) > 10:
            score += 0.2

        # 내용이 충분히 긺 (30점)
        content_length = len(item.content or "")
        if content_length > 100:
            score += 0.2
        if content_length > 500:
            score += 0.1

        # 작성자 정보 있음 (10점)
        if item.author:
            score += 0.1

        # 날짜 정보 있음 (10점)
        if item.date:
            score += 0.1

        # 조회수/좋아요 수 (15점)
        if item.views > 0 or item.likes > 0:
            score += 0.15

        # 이미지 있음 (15점)
        if item.image_urls:
            score += 0.15

        return min(1.0, score)

    def is_valid_item(self, item: CrawledItem) -> bool:
        """
        아이템 유효성 검사

        Args:
            item: 검사할 아이템

        Returns:
            유효성 여부
        """
        # 기본 필드 확인
        if not item.url:
            return False

        # 내용이 너무 짧으면 제외
        content_length = len(item.content or "")
        title_length = len(item.title or "")
        min_length = YOUTUBE_MIN_CONTENT_LENGTH if item.platform == "youtube" else DEFAULT_MIN_CONTENT_LENGTH
        if content_length < min_length and title_length < min_length:
            return False

        # 스팸성 콘텐츠 필터링
        spam_patterns = ['광고', '할인', '구매', '판매', '클릭', '바로가기']
        text_lower = (item.title + " " + item.content).lower()
        spam_count = sum(1 for pattern in spam_patterns if pattern in text_lower)

        # 스팸 단어가 너무 많으면 제외
        if spam_count > 3:
            return False

        return True

    async def post_process_items(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """
        수집된 아이템 후처리

        Args:
            items: 후처리할 아이템 목록

        Returns:
            후처리된 아이템 목록
        """
        processed_items = []

        for item in items:
            # 텍스트 정제
            item.title = clean_text(item.title)
            item.content = clean_text(item.content)

            # 패션 키워드 추출
            full_text = item.title + " " + item.content
            item.fashion_tags = extract_fashion_keywords(full_text)

            # 상품 링크 추출
            item.product_links = extract_product_links(full_text)

            # 이미지 URL 추출
            item.image_urls = extract_image_urls(full_text)

            # 품질 점수 계산
            item.quality_score = self.calculate_quality_score(item)

            # 관련성 점수 (패션 키워드 기반)
            if item.fashion_tags:
                item.relevance_score = min(1.0, len(item.fashion_tags) * 0.2)
            else:
                # 내용에 패션 관련 단어가 있는지 확인
                fashion_words = ['옷', '패션', '코디', '스타일', '의상']
                relevance = sum(1 for word in fashion_words if word in full_text.lower())
                item.relevance_score = min(1.0, relevance * 0.3)

            # 유효성 검사
            if self.is_valid_item(item):
                processed_items.append(item)

        return processed_items
