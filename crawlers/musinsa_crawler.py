"""
Musinsa fashion crawler
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import json
import re
import logging

from .base_crawler import BaseCrawler, CrawledItem
from .common import NetworkUtils, DateUtils, TextUtils

logger = logging.getLogger(__name__)


class MusinsaCrawler(BaseCrawler):
    """무신사 쇼핑몰 크롤러"""

    def __init__(self, config: dict = None):
        super().__init__(config)

        self.base_url = "https://www.musinsa.com"
        self.api_base = "https://www.musinsa.com/app"

        # API 엔드포인트
        self.endpoints = {
            'search': f"{self.api_base}/search/goods",
            'trend': f"{self.api_base}/trend/style/list",
            'magazine': f"{self.api_base}/magazine/list",
            'ranking': f"{self.api_base}/ranking/best",
        }

        # 브랜드 카테고리
        self.brand_categories = [
            'street', 'casual', 'sports', 'luxury',
            'minimal', 'vintage', 'feminine', 'hiphop'
        ]

    def get_channel_name(self) -> str:
        return "Musinsa"

    async def crawl(
        self,
        keyword: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CrawledItem]:
        """
        무신사 크롤링

        Args:
            keyword: 검색 키워드
            start_date: 시작일
            end_date: 종료일

        Returns:
            수집된 데이터 목록
        """
        items = []

        # 1. 상품 검색 결과
        try:
            product_items = await self._crawl_products(keyword)
            items.extend(product_items)
        except Exception as e:
            logger.error(f"Failed to crawl products: {e}")

        # 2. 스타일 추천
        try:
            style_items = await self._crawl_styles(keyword, start_date, end_date)
            items.extend(style_items)
        except Exception as e:
            logger.error(f"Failed to crawl styles: {e}")

        # 3. 매거진 콘텐츠
        try:
            magazine_items = await self._crawl_magazine(keyword, start_date, end_date)
            items.extend(magazine_items)
        except Exception as e:
            logger.error(f"Failed to crawl magazine: {e}")

        # 4. 랭킹 상품
        try:
            ranking_items = await self._crawl_rankings()
            items.extend(ranking_items)
        except Exception as e:
            logger.error(f"Failed to crawl rankings: {e}")

        # 중복 제거 및 품질 필터링
        unique_items = self._remove_duplicates(items)
        filtered_items = [item for item in unique_items if item.quality_score > 0.3]

        # 최대 개수 제한
        return filtered_items[:self.max_items]

    async def _crawl_products(self, keyword: str) -> List[CrawledItem]:
        """상품 크롤링"""
        items = []

        # 검색 API 호출
        search_url = f"{self.endpoints['search']}"
        params = {
            'keyword': keyword,
            'listKind': 'search',
            'sortCd': 'popular',
            'page': 1,
            'size': 20
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, params=params) as response:
                if response.status != 200:
                    return items

                data = await response.json()

                # 상품 목록 파싱
                if 'data' in data and 'list' in data['data']:
                    for product in data['data']['list']:
                        item = await self._parse_product(product)
                        if item:
                            items.append(item)

        return items

    async def _crawl_styles(
        self,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        """스타일 추천 크롤링"""
        items = []

        # 스타일 API 호출
        style_url = f"{self.endpoints['trend']}"
        params = {
            'keyword': keyword,
            'page': 1,
            'size': 20
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(style_url, params=params) as response:
                if response.status != 200:
                    return items

                data = await response.json()

                # 스타일 목록 파싱
                if 'data' in data:
                    for style in data.get('styles', []):
                        # 날짜 필터링
                        created_at = DateUtils.parse_date_string(style.get('created_at'))
                        if not DateUtils.is_date_in_range(created_at, start_date, end_date):
                            continue

                        item = await self._parse_style(style)
                        if item:
                            items.append(item)

        return items

    async def _crawl_magazine(
        self,
        keyword: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[CrawledItem]:
        """매거진 콘텐츠 크롤링"""
        items = []

        # 매거진 API 호출
        magazine_url = f"{self.endpoints['magazine']}"
        params = {
            'keyword': keyword,
            'page': 1,
            'size': 20
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(magazine_url, params=params) as response:
                if response.status != 200:
                    return items

                data = await response.json()

                # 매거진 목록 파싱
                if 'data' in data:
                    for article in data.get('magazines', []):
                        # 날짜 필터링
                        published_at = DateUtils.parse_date_string(article.get('published_at'))
                        if not DateUtils.is_date_in_range(published_at, start_date, end_date):
                            continue

                        item = await self._parse_magazine(article)
                        if item:
                            items.append(item)

        return items

    async def _crawl_rankings(self) -> List[CrawledItem]:
        """랭킹 상품 크롤링"""
        items = []

        # 랭킹 API 호출
        ranking_url = f"{self.endpoints['ranking']}"
        params = {
            'category': 'total',
            'period': 'daily',
            'page': 1,
            'size': 20
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(ranking_url, params=params) as response:
                if response.status != 200:
                    return items

                data = await response.json()

                # 랭킹 목록 파싱
                if 'data' in data:
                    for rank, product in enumerate(data.get('ranking', []), 1):
                        item = await self._parse_ranking_product(product, rank)
                        if item:
                            items.append(item)

        return items

    async def _parse_product(self, product: dict) -> Optional[CrawledItem]:
        """상품 정보 파싱"""
        try:
            # 기본 정보
            title = product.get('goodsName', '')
            brand = product.get('brandName', '')
            price = product.get('price', 0)
            original_price = product.get('originalPrice', 0)
            discount_rate = product.get('discountRate', 0)

            # URL
            goods_no = product.get('goodsNo', '')
            url = f"{self.base_url}/goods/{goods_no}"

            # 이미지
            image_url = product.get('imageUrl', '')
            if image_url and not image_url.startswith('http'):
                image_url = f"https:{image_url}"

            # 설명
            description = f"{brand} {title}"
            if discount_rate > 0:
                description += f" (혜택 {discount_rate}%)"

            # 카테고리 및 태그
            category_name = product.get('categoryName', '')
            tags = product.get('tags', [])

            item = CrawledItem(
                title=title,
                content=description,
                url=url,
                platform="musinsa",
                source_id=f"goods_{goods_no}",
                image_urls=[image_url] if image_url else [],
                fashion_tags=tags,
                product_links=[url],
                metadata={
                    'brand': brand,
                    'price': price,
                    'original_price': original_price,
                    'discount_rate': discount_rate,
                    'category': category_name,
                    'type': 'product'
                }
            )

            # 품질 점수
            item.quality_score = self._calculate_product_quality_score(product)
            item.relevance_score = 1.0 if tags else 0.7

            return item

        except Exception as e:
            logger.error(f"Error parsing product: {e}")
            return None

    async def _parse_style(self, style: dict) -> Optional[CrawledItem]:
        """스타일 정보 파싱"""
        try:
            title = style.get('title', '')
            description = style.get('description', '')
            style_no = style.get('styleNo', '')
            url = f"{self.base_url}/styles/{style_no}"

            # 이미지
            image_url = style.get('imageUrl', '')
            if image_url and not image_url.startswith('http'):
                image_url = f"https:{image_url}"

            # 태그
            tags = style.get('tags', [])
            goods_list = style.get('goodsList', [])

            # 상품 링크
            product_links = []
            for goods in goods_list[:5]:  # 최대 5개 상품
                goods_no = goods.get('goodsNo', '')
                if goods_no:
                    product_links.append(f"{self.base_url}/goods/{goods_no}")

            item = CrawledItem(
                title=title,
                content=description,
                url=url,
                platform="musinsa",
                source_id=f"style_{style_no}",
                image_urls=[image_url] if image_url else [],
                fashion_tags=tags,
                product_links=product_links,
                metadata={
                    'type': 'style',
                    'goods_count': len(goods_list),
                    'likes': style.get('likes', 0)
                }
            )

            return item

        except Exception as e:
            logger.error(f"Error parsing style: {e}")
            return None

    async def _parse_magazine(self, article: dict) -> Optional[CrawledItem]:
        """매거진 기사 파싱"""
        try:
            title = article.get('title', '')
            content = article.get('content', '')
            article_no = article.get('articleNo', '')
            url = f"{self.base_url}/magazine/{article_no}"

            # 이미지
            image_url = article.get('imageUrl', '')
            if image_url and not image_url.startswith('http'):
                image_url = f"https:{image_url}"

            # 작성자
            author = article.get('writerName', '')

            # 태그
            tags = article.get('tags', [])

            item = CrawledItem(
                title=title,
                content=content,
                url=url,
                author=author,
                platform="musinsa",
                source_id=f"magazine_{article_no}",
                image_urls=[image_url] if image_url else [],
                fashion_tags=tags,
                metadata={
                    'type': 'magazine',
                    'views': article.get('views', 0),
                    'category': article.get('categoryName', '')
                }
            )

            return item

        except Exception as e:
            logger.error(f"Error parsing magazine: {e}")
            return None

    async def _parse_ranking_product(self, product: dict, rank: int) -> Optional[CrawledItem]:
        """랭킹 상품 파싱"""
        try:
            title = product.get('goodsName', '')
            brand = product.get('brandName', '')
            price = product.get('price', 0)
            goods_no = product.get('goodsNo', '')
            url = f"{self.base_url}/goods/{goods_no}"

            # 이미지
            image_url = product.get('imageUrl', '')
            if image_url and not image_url.startswith('http'):
                image_url = f"https:{image_url}"

            # 랭킹 정보를 포함한 제목
            title_with_rank = f"[{rank}위] {brand} {title}"

            item = CrawledItem(
                title=title_with_rank,
                content=f"{brand} {title} - {price}원",
                url=url,
                platform="musinsa",
                source_id=f"ranking_{goods_no}",
                image_urls=[image_url] if image_url else [],
                product_links=[url],
                metadata={
                    'type': 'ranking',
                    'rank': rank,
                    'brand': brand,
                    'price': price
                }
            )

            return item

        except Exception as e:
            logger.error(f"Error parsing ranking product: {e}")
            return None

    def _calculate_product_quality_score(self, product: dict) -> float:
        """상품 품질 점수 계산"""
        score = 0.0

        # 브랜드 정보 (20점)
        if product.get('brandName'):
            score += 0.2

        # 이미지 (20점)
        if product.get('imageUrl'):
            score += 0.2

        # 가격 정보 (15점)
        if product.get('price') and product.get('price') > 0:
            score += 0.15

        # 할인 (15점)
        if product.get('discountRate', 0) > 0:
            score += 0.15

        # 태그 (15점)
        if product.get('tags'):
            score += 0.15

        # 상세 설명 (15점)
        if len(product.get('goodsName', '')) > 10:
            score += 0.15

        return min(1.0, score)

    def _remove_duplicates(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """중복 제거"""
        seen_urls = set()
        unique_items = []

        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)

        return unique_items