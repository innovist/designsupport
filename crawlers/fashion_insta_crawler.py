"""
Fashion Instagram crawler
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import logging

from .base_crawler import BaseCrawler, CrawledItem
from .common import NetworkUtils, DateUtils

logger = logging.getLogger(__name__)


class FashionInstaCrawler(BaseCrawler):
    """패션 인스타그램 크롤러"""

    def __init__(self, config: dict = None):
        super().__init__(config)

        # 패션 인플루언서 계정 목록
        self.fashion_accounts = [
            "voguekorea",
            "ellekorea",
            "harpersbazaarkr",
            "marieclairekorea",
            "cosmopolitankr",
            "wdkorea",
            "fashionnet_kr",
            "musb_seoul",
            "29cm_official",
            "nike",
            "adidasoriginals",
            "zara",
            "hmkr",
            "uniqlo_kr",
            "gap_korea",
            "spao_official",
            "8seconds_kr"
        ]

        # 패션 관련 해시태그
        self.fashion_hashtags = [
            "패션", "fashion", "코디", "styling", "ootd", " outfit",
            "스타일", "style", "의상", "lookbook", "패션스타그램",
            "fashionista", "streetstyle", "패션인스타", "데일리룩"
        ]

        # API 엔드포인트
        self.graphql_url = "https://www.instagram.com/graphql/query"

    def get_channel_name(self) -> str:
        return "Fashion Instagram"

    async def crawl(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        """
        인스타그램 크롤링

        Args:
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일

        Returns:
            수집된 포스트 목록
        """
        items = []

        # 1. 패션 인플루언서 포스트 수집
        for account in self.fashion_accounts:
            try:
                account_items = await self._crawl_account_posts(
                    account, keyword, start_date, end_date
                )
                items.extend(account_items)

                # 딜레이 적용
                if self.delay > 0:
                    await asyncio.sleep(self.delay)

            except Exception as e:
                logger.error(f"Failed to crawl account {account}: {e}")

        # 2. 해시태그 포스트 수집
        hashtags = self._generate_hashtags(keyword)
        for hashtag in hashtags[:10]:  # 최대 10개 해시태그
            try:
                hashtag_items = await self._crawl_hashtag_posts(
                    hashtag, start_date, end_date
                )
                items.extend(hashtag_items)

                # 딜레이 적용
                if self.delay > 0:
                    await asyncio.sleep(self.delay)

            except Exception as e:
                logger.error(f"Failed to crawl hashtag {hashtag}: {e}")

        # 중복 제거 및 품질 필터링
        unique_items = self._remove_duplicates(items)
        filtered_items = [item for item in unique_items if item.quality_score > 0.4]

        # 최대 개수 제한
        return filtered_items[:self.max_items]

    async def _crawl_account_posts(
        self,
        username: str,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        """계정 포스트 크롤링"""
        items = []

        # 사용자 ID 조회
        user_id = await self._get_user_id(username)
        if not user_id:
            return items

        # 최근 포스트 조회
        posts = await self._get_user_posts(user_id, 12)  # 최근 12개

        for post in posts:
            # 키워드 필터링
            if keyword and not self._contains_keyword(post, keyword):
                continue

            # 날짜 필터링
            post_date = datetime.fromtimestamp(post.get('taken_at_timestamp', 0))
            if not DateUtils.is_date_in_range(post_date, start_date, end_date):
                continue

            # CrawledItem 생성
            item = await self._post_to_item(post, username, "account")
            if item:
                items.append(item)

        return items

    async def _crawl_hashtag_posts(
        self,
        hashtag: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        """해시태그 포스트 크롤링"""
        items = []

        # 해시태그 정보 조회
        hashtag_info = await self._get_hashtag_info(hashtag)
        if not hashtag_info:
            return items

        # 최근 포스트 조회
        posts = await self._get_hashtag_posts(hashtag_info['id'], 12)

        for post in posts:
            # 날짜 필터링
            post_date = datetime.fromtimestamp(post.get('taken_at_timestamp', 0))
            if not DateUtils.is_date_in_range(post_date, start_date, end_date):
                continue

            # CrawledItem 생성
            item = await self._post_to_item(post, hashtag, "hashtag")
            if item:
                items.append(item)

        return items

    async def _get_user_id(self, username: str) -> Optional[str]:
        """사용자 ID 조회"""
        # 실제로는 Instagram GraphQL API 호출 필요
        # 여기서는 가상의 구현
        return f"user_{username}"

    async def _get_user_posts(self, user_id: str, count: int = 12) -> List[dict]:
        """사용자 포스트 조회"""
        # 실제로는 Instagram GraphQL API 호출 필요
        # 여기서는 가상 데이터 반환
        return []

    async def _get_hashtag_info(self, hashtag: str) -> Optional[dict]:
        """해시태그 정보 조회"""
        # 실제로는 Instagram GraphQL API 호출 필요
        return {"id": f"hashtag_{hashtag}"}

    async def _get_hashtag_posts(self, hashtag_id: str, count: int = 12) -> List[dict]:
        """해시태그 포스트 조회"""
        # 실제로는 Instagram GraphQL API 호출 필요
        return []

    def _contains_keyword(self, post: dict, keyword: str) -> bool:
        """포스트에 키워드 포함 여부"""
        text = f"{post.get('caption', '')} {post.get('accessibility_caption', '')}"
        return keyword.lower() in text.lower()

    async def _post_to_item(
        self,
        post: dict,
        source: str,
        source_type: str
    ) -> Optional[CrawledItem]:
        """포스트를 CrawledItem으로 변환"""
        try:
            # 기본 정보
            caption = post.get('caption', '')
            if not caption:
                caption = post.get('accessibility_caption', '')

            # URL 생성
            shortcode = post.get('shortcode', '')
            url = f"https://www.instagram.com/p/{shortcode}/" if shortcode else ""

            # 이미지 URL
            image_urls = []
            if 'display_url' in post:
                image_urls.append(post['display_url'])

            # 여러 이미지
            if 'edge_sidecar_to_children' in post:
                edges = post['edge_sidecar_to_children'].get('edges', [])
                for edge in edges:
                    node = edge.get('node', {})
                    if 'display_url' in node:
                        image_urls.append(node['display_url'])

            # 좋아요 및 댓글 수
            likes = post.get('edge_media_preview_like', {}).get('count', 0)
            comments = post.get('edge_media_to_comment', {}).get('count', 0)

            # 작성자
            owner = post.get('owner', {})
            author = owner.get('username', '')

            # 해시태그 추출
            hashtags = self._extract_hashtags(caption)

            # 위치 정보
            location = post.get('location', {})
            location_name = location.get('name', '') if location else ''

            # 제목 (캡션의 첫 줄)
            title = caption.split('\n')[0][:100]
            if len(title) < 10:
                title = f"Instagram post by {author}"

            item = CrawledItem(
                title=title,
                content=caption,
                url=url,
                author=author,
                date=datetime.fromtimestamp(post.get('taken_at_timestamp', 0)),
                likes=likes,
                comments=comments,
                platform="instagram",
                source_id=post.get('id', ''),
                image_urls=image_urls,
                fashion_tags=hashtags,
                metadata={
                    'source': source,
                    'source_type': source_type,
                    'location': location_name,
                    'media_type': post.get('media_type', 'image'),
                    'is_video': post.get('is_video', False)
                }
            )

            return item

        except Exception as e:
            logger.error(f"Error converting post to item: {e}")
            return None

    def _extract_hashtags(self, caption: str) -> List[str]:
        """캡션에서 해시태그 추출"""
        import re
        hashtags = re.findall(r'#(\w+)', caption.lower())
        return [tag for tag in hashtags if tag in [h.lower().replace('#', '') for h in self.fashion_hashtags]]

    def _generate_hashtags(self, keyword: str) -> List[str]:
        """키워드 기반 해시태그 생성"""
        hashtags = []

        # 기본 패션 해시태그 추가
        hashtags.extend(self.fashion_hashtags[:5])

        # 키워드 관련 해시태그
        if keyword:
            keyword_lower = keyword.lower()
            hashtags.append(keyword_lower)
            hashtags.append(f"{keyword_lower}style")
            hashtags.append(f"{keyword_lower}fashion")
            hashtags.append(f"{keyword_lower}ootd")

        return hashtags

    def _remove_duplicates(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """중복 제거"""
        seen_ids = set()
        unique_items = []

        for item in items:
            if item.source_id not in seen_ids:
                seen_ids.add(item.source_id)
                unique_items.append(item)

        return unique_items