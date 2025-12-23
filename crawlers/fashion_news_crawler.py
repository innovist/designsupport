"""
Fashion news crawler
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
import feedparser
import logging

from .base_crawler import BaseCrawler, CrawledItem
from .common import NetworkUtils, DateUtils, TextUtils
from .fashion_news_parsers import (
    parse_vogue_search,
    parse_elle_search,
    parse_harpers_search,
    parse_fashion_network_search
)

logger = logging.getLogger(__name__)


class FashionNewsCrawler(BaseCrawler):
    """패션 뉴스 크롤러"""

    def __init__(self, config: dict = None):
        super().__init__(config)

        # 패션 뉴스 RSS 피드 목록
        self.rss_feeds = [
            {
                "name": "Vogue Korea",
                "url": "https://www.vogue.co.kr/feed/",
                "platform": "vogue_korea"
            },
            {
                "name": "Elle Korea",
                "url": "https://www.elle.co.kr/rss",
                "platform": "elle_korea"
            },
            {
                "name": "Harper's Bazaar Korea",
                "url": "https://www.harpersbazaar.co.kr/rss",
                "platform": "harpersbazaar_korea"
            },
            {
                "name": "WWD",
                "url": "https://wwd.com/feed/",
                "platform": "wwd"
            },
            {
                "name": "Fashion Network",
                "url": "https://www.fashionnetwork.com/rss/news/korea",
                "platform": "fashion_network"
            }
        ]

        # 검색 키워드별 사이트 URL
        self.search_urls = {
            "vogue_korea": "https://www.vogue.co.kr/search/?q={keyword}",
            "elle_korea": "https://www.elle.co.kr/search?query={keyword}",
            "harpersbazaar_korea": "https://www.harpersbazaar.co.kr/search?query={keyword}",
            "fashion_network": "https://www.fashionnetwork.com/news/search/keyword/{keyword}"
        }

    def get_channel_name(self) -> str:
        return "Fashion News"

    async def crawl(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        """
        패션 뉴스 크롤링

        Args:
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일

        Returns:
            수집된 뉴스 목록
        """
        items = await self._collect_rss_items(start_date, end_date)
        items.extend(await self._collect_search_items(keyword, start_date, end_date))

        # 중복 제거 및 품질 필터링
        unique_items = self._remove_duplicates(items)
        processed_items = await self.post_process_items(unique_items)
        filtered_items = [item for item in processed_items if item.quality_score > 0.3]

        # 최대 개수 제한
        return filtered_items[:self.max_items]

    async def _collect_rss_items(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        items: List[CrawledItem] = []
        for feed_info in self.rss_feeds:
            try:
                feed_items = await self._crawl_rss_feed(feed_info, start_date, end_date)
                items.extend(feed_items)
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
            except Exception as e:
                logger.error(f"Failed to crawl RSS feed {feed_info['name']}: {e}")
        return items

    async def _collect_search_items(
        self,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        items: List[CrawledItem] = []
        if not keyword:
            return items
        for platform, url_template in self.search_urls.items():
            try:
                search_items = await self._crawl_search_results(
                    platform,
                    url_template.format(keyword=keyword),
                    keyword,
                    start_date,
                    end_date
                )
                items.extend(search_items)
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
            except Exception as e:
                logger.error(f"Failed to crawl search results for {platform}: {e}")
        return items

    async def _crawl_rss_feed(
        self,
        feed_info: dict,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        """RSS 피드 크롤링"""
        items = []

        try:
            # RSS 파싱
            feed = feedparser.parse(feed_info['url'])
            platform = feed_info['platform']

            for entry in feed.entries:
                # 날짜 필터링
                published_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])

                if not DateUtils.is_date_in_range(published_date, start_date, end_date):
                    continue

                # CrawledItem 생성
                item = CrawledItem(
                    title=entry.get('title', ''),
                    content=entry.get('description', ''),
                    url=entry.get('link', ''),
                    author=entry.get('author', ''),
                    date=published_date,
                    platform=platform,
                    source_id=entry.get('id', ''),
                    metadata={
                        'feed_name': feed_info['name'],
                        'tags': [tag.term for tag in entry.get('tags', [])]
                    }
                )

                # 이미지 URL 추출
                if hasattr(entry, 'media_content'):
                    for media in entry.media_content:
                        if media.get('type', '').startswith('image/'):
                            item.image_urls.append(media['url'])

                items.append(item)

                # 최대 개수 체크
                if len(items) >= self.max_items // len(self.rss_feeds):
                    break

        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_info['name']}: {e}")

        return items

    async def _crawl_search_results(
        self,
        platform: str,
        url: str,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        """검색 결과 크롤링"""
        items = []

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return items

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # 플랫폼별로 다른 선택자 사용
                if platform == "vogue_korea":
                    items = await parse_vogue_search(soup, platform, keyword)
                elif platform == "elle_korea":
                    items = await parse_elle_search(soup, platform, keyword)
                elif platform == "harpersbazaar_korea":
                    items = await parse_harpers_search(soup, platform, keyword)
                elif platform == "fashion_network":
                    items = await parse_fashion_network_search(soup, platform, keyword)

        # 날짜 필터링
        filtered_items = []
        for item in items:
            if DateUtils.is_date_in_range(item.date, start_date, end_date):
                filtered_items.append(item)

        return filtered_items

    def _remove_duplicates(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """중복 제거"""
        seen_urls = set()
        unique_items = []

        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        return unique_items
