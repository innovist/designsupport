"""
Data processing service for crawled fashion data
"""

import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datasketch import MinHash
import numpy as np
import jieba
import jieba.analyse
from konlpy.tag import Okt
import logging

from app.models.crawler import RawData, Comment, CrawlJob
from crawlers.base_crawler import CrawledItem
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingStats:
    """처리 통계 정보"""
    total_items: int = 0
    processed_items: int = 0
    duplicates_removed: int = 0
    low_quality_removed: int = 0
    spam_removed: int = 0
    quality_score_avg: float = 0.0
    relevance_score_avg: float = 0.0


class DataProcessor:
    """데이터 처리 서비스"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        초기화

        Args:
            config: 처리 설정
        """
        self.config = config or {}

        # 품질 필터링 임계값
        self.quality_threshold = self.config.get('quality_threshold', 0.3)
        self.relevance_threshold = self.config.get('relevance_threshold', 0.3)

        # 중복 제거 설정
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)
        self.num_permutations = self.config.get('num_permutations', 128)

        # 한국어 분석기 초기화
        try:
            self.okt = Okt()
            logger.info("Okt tokenizer loaded")
        except:
            self.okt = None
            logger.warning("Okt tokenizer not available, using fallback")

        # 불용어 사전
        self.stop_words = self._load_stop_words()

        # 패션 키워드 사전
        self.fashion_keywords = self._load_fashion_keywords()

    def _load_stop_words(self) -> Set[str]:
        """불용어 사전 로드"""
        # 기본 한국어 불용어
        korean_stop_words = {
            '이', '그', '저', '의', '를', '에', '와', '은', '는', '로', '으로',
            '에서', '으로서', '에게', '에게서', '까지', '부터', '보다', '처럼',
            '같이', '하고', '하며', '하지만', '그리고', '그러나', '따라서',
            '하다', '있다', '되다', '같다', '이다', '하며', '하지', '안',
            '더', '수', '있', '없', '있습니다', '합니다', '있을', '합니다',
            # 영어 불용어
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from'
        }

        return korean_stop_words

    def _load_fashion_keywords(self) -> Dict[str, List[str]]:
        """패션 키워드 사전 로드"""
        return {
            'clothing': [
                '티셔츠', '블라우스', '셔츠', '니트', '스웨터', '가디건',
                '바지', '청바지', '슬랙스', '진', '면바지', '반바지',
                '치마', '스커트', '드레스', '원피스', '점프수트',
                '자켓', '재킷', '코트', '점퍼', '블레이저',
                '맨투맨', '후드', '조끼',
                'shirt', 'blouse', 'knit', 'sweater', 'pants', 'jeans',
                'skirt', 'dress', 'jacket', 'coat', 'jumper'
            ],
            'material': [
                '코튼', '린넨', '울', '실크', '데님', '레이스', '가죽',
                '폴리에스터', '나일론', '아크릴', '스판덱스',
                'velvet', 'leather', 'denim', 'cotton', 'silk'
            ],
            'color': [
                '블랙', '화이트', '그레이', '베이지', '네이비', '브라운',
                '레드', '블루', '그린', '옐로우', '핑크',
                'black', 'white', 'gray', 'beige', 'red', 'blue'
            ],
            'style': [
                '미니멀', '캐주얼', '스트릿', '포멀', '비즈니스',
                '빈티지', '레트로', '모던', '클래식', '스트릿',
                'minimal', 'casual', 'vintage', 'street style'
            ],
            'pattern': [
                '체크', '스트라이프', '도트', '플로럴', '카모',
                'animal', 'geometric', 'abstract',
                'check', 'stripe', 'floral', 'camo'
            ]
        }

    async def process_crawled_data(
        self,
        items: List[CrawledItem],
        crawl_job_id: int
    ) -> ProcessingStats:
        """
        크롤링된 데이터 처리

        Args:
            items: 처리할 아이템 목록
            crawl_job_id: 크롤링 작업 ID

        Returns:
            처리 통계
        """
        stats = ProcessingStats(total_items=len(items))

        # 1. 중복 제거
        unique_items = self._remove_duplicates(items)
        stats.duplicates_removed = len(items) - len(unique_items)
        logger.info(f"Removed {stats.duplicates_removed} duplicates")

        # 2. 품질 필터링
        quality_items = self._filter_quality(unique_items)
        stats.low_quality_removed = len(unique_items) - len(quality_items)
        logger.info(f"Removed {stats.low_quality_removed} low quality items")

        # 3. 스팸 필터링
        final_items = self._filter_spam(quality_items)
        stats.spam_removed = len(quality_items) - len(final_items)
        logger.info(f"Removed {stats.spam_removed} spam items")

        # 4. 후처리
        processed_items = []
        for item in final_items:
            processed_item = await self._post_process_item(item)
            processed_items.append(processed_item)

        stats.processed_items = len(processed_items)

        # 평균 점수 계산
        if processed_items:
            stats.quality_score_avg = sum(item.quality_score for item in processed_items) / len(processed_items)
            stats.relevance_score_avg = sum(item.relevance_score for item in processed_items) / len(processed_items)

        # 5. 데이터베이스 저장
        await self._save_to_database(processed_items, crawl_job_id)

        logger.info(f"Processing completed: {stats.processed_items}/{stats.total_items} items")
        return stats

    def _remove_duplicates(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """중복 제거"""
        unique_items = []
        seen_urls = set()
        seen_hashes = set()
        minhashes = {}

        # 첫 번째 패스: URL 기반 중복 제거
        for item in items:
            if item.url and item.url in seen_urls:
                continue
            if item.url:
                seen_urls.add(item.url)
            unique_items.append(item)

        # 두 번째 패스: 내용 유사도 기반 중복 제거
        final_items = []
        for item in unique_items:
            # 콘텐츠 해시 생성
            content = (item.title + " " + item.content).lower()
            content_hash = hashlib.md5(content.encode()).hexdigest()

            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)

            # MinHash 생성 (성능을 위해 일부만)
            if len(final_items) < 1000:  # 1000개까지만 MinHash 계산
                minhash = MinHash(num_permutations=self.num_permutations)
                words = self._extract_words(content)
                for word in words:
                    minhash.update(word.encode())

                # 유사도 체크
                is_duplicate = False
                for existing_hash, existing_minhash in minhashes.items():
                    similarity = minhash.jaccard(existing_minhash)
                    if similarity > self.similarity_threshold:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    minhashes[content_hash] = minhash
                    final_items.append(item)
                else:
                    # 기존 아이템의 메타데이터에 중복 정보 추가
                    for existing_item in final_items:
                        existing_item.metadata.setdefault('duplicates', [])
                        existing_item.metadata['duplicates'].append(item.url)

            else:
                final_items.append(item)

        return final_items

    def _filter_quality(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """품질 필터링"""
        quality_items = []

        for item in items:
            # 미리 계산된 품질 점수 확인
            if item.quality_score >= self.quality_threshold:
                # 추가 품질 검사
                if self._is_high_quality(item):
                    quality_items.append(item)

        return quality_items

    def _is_high_quality(self, item: CrawledItem) -> bool:
        """고품질 여부 확인"""
        # 내용 길이
        content_length = len(item.content or "")
        if content_length < 50:
            return False

        # 이미지 있음
        if not item.image_urls:
            return False

        # 스팸성 패턴 체크
        spam_patterns = [
            r'무료.*다운로드',
            r'바로가기',
            r'클릭.*필수',
            r'구매.*할인',
            r'광고.*문의'
        ]

        combined_text = (item.title + " " + item.content).lower()
        for pattern in spam_patterns:
            if re.search(pattern, combined_text):
                return False

        return True

    def _filter_spam(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """스팸 필터링"""
        filtered_items = []

        for item in items:
            # 패션 관련성 확인
            if self._is_fashion_related(item):
                filtered_items.append(item)

        return filtered_items

    def _is_fashion_related(self, item: CrawledItem) -> bool:
        """패션 관련성 확인"""
        combined_text = (item.title + " " + item.content + " " + " ".join(item.fashion_tags)).lower()

        # 패션 키워드 점수
        fashion_score = 0
        for category, keywords in self.fashion_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    fashion_score += 1

        # 패션 관련 단어 개수 기준
        return fashion_score >= 1

    async def _post_process_item(self, item: CrawledItem) -> CrawledItem:
        """아이템 후처리"""
        # 텍스트 정제
        item.title = self._clean_text(item.title)
        item.content = self._clean_text(item.content)

        # 패션 키워드 재추출
        full_text = item.title + " " + item.content
        item.fashion_tags = self._extract_fashion_keywords(full_text)

        # 상품 링크 재추출
        item.product_links = self._extract_product_links(full_text)

        # 관련성 점수 재계산
        item.relevance_score = self._calculate_relevance_score(item)

        return item

    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""

        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)

        # 특수문자 제거
        text = re.sub(r'[^\w\s\u3131-\u3163\uac00-\ud7a3.,!?~\-]', '', text)

        # 여러 공백 제거
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _extract_words(self, text: str) -> List[str]:
        """단어 추출"""
        if not text:
            return []

        words = []

        # 형태소 분석 (사용 가능한 경우)
        if self.okt:
            try:
                tagged = self.okt.pos(text, norm=True, stem=True)
                words = [word for word, pos in tagged if pos in ['Noun', 'Adjective', 'Verb'] and len(word) > 1]
            except Exception as e:
                logger.warning(f"Okt analysis failed: {e}")
                words = []

        # 형태소 분석 실패 시 단순 분할
        if not words:
            words = re.findall(r'\b\w+\b', text.lower())

        # 불용어 필터링
        words = [word for word in words if word not in self.stop_words and len(word) > 1]

        return words

    def _extract_fashion_keywords(self, text: str) -> List[str]:
        """패션 키워드 추출"""
        keywords = set()
        text_lower = text.lower()

        for category, keyword_list in self.fashion_keywords.items():
            for keyword in keyword_list:
                if keyword in text_lower:
                    keywords.add(keyword)

        return list(keywords)

    def _extract_product_links(self, text: str) -> List[str]:
        """상품 링크 추출"""
        # URL 패턴
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)

        # 쇼핑몰 도메인 필터링
        shopping_domains = [
            'musinsa', '29cm', 'abcmart', 'nike', 'adidas',
            'zara', 'uniqlo', 'hm', 'gap', 'forever21',
            'spao', '8seconds', 'thehyundai', 'lfmall'
        ]

        product_links = []
        for url in urls:
            if any(domain in url.lower() for domain in shopping_domains):
                product_links.append(url)

        return product_links

    def _calculate_relevance_score(self, item: CrawledItem) -> float:
        """관련성 점수 계산"""
        score = 0.0

        # 패션 키워드 기반 (40점)
        if item.fashion_tags:
            score += min(0.4, len(item.fashion_tags) * 0.1)

        # 상품 링크 기반 (30점)
        if item.product_links:
            score += min(0.3, len(item.product_links) * 0.1)

        # 이미지 기반 (20점)
        if item.image_urls:
            score += min(0.2, len(item.image_urls) * 0.05)

        # 콘텐츠 품질 기반 (10점)
        content_length = len(item.content or "")
        if content_length > 100:
            score += 0.1

        return min(1.0, score)

    async def _save_to_database(self, items: List[CrawledItem], crawl_job_id: int):
        """데이터베이스 저장"""
        # 실제 구현 시 SQLAlchemy ORM 사용
        # 여기서는 로그만 남김
        logger.info(f"Saving {len(items)} items to database for crawl_job_id={crawl_job_id}")

        for item in items:
            # RawData 모델에 저장
            raw_data = RawData(
                crawl_job_id=crawl_job_id,
                source=item.platform,
                url=item.url,
                title=item.title,
                content=item.content,
                quality_score=item.quality_score,
                relevance_score=item.relevance_score,
                content_hash=hashlib.md5((item.title + item.content).encode()).hexdigest()
            )

            # 실제 저장은 여기서 생략
            logger.debug(f"Would save: {raw_data.title[:50]}...")

    async def analyze_data_quality(self, crawl_job_id: int) -> Dict[str, Any]:
        """데이터 품질 분석"""
        # 실제 구현 시 DB에서 데이터 조회
        return {
            "total_items": 0,
            "avg_quality_score": 0.0,
            "avg_relevance_score": 0.0,
            "fashion_keyword_coverage": 0.0,
            "image_ratio": 0.0,
            "duplicate_ratio": 0.0
        }
