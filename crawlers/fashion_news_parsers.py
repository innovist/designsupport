"""
Parser helpers for fashion news crawler
"""

from typing import List
from bs4 import BeautifulSoup
import logging

from .base_crawler import CrawledItem
from .common import DateUtils

logger = logging.getLogger(__name__)


async def parse_vogue_search(
    soup: BeautifulSoup,
    platform: str,
    keyword: str
) -> List[CrawledItem]:
    """Vogue 검색 결과 파싱"""
    items: List[CrawledItem] = []
    articles = soup.find_all('article', class_='article-item') or \
        soup.find_all('div', class_='search-result-item')
    for article in articles:
        try:
            title_elem = article.find('h2') or article.find('h3')
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            link_elem = title_elem.find('a')
            if not link_elem:
                continue
            url = link_elem.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://www.vogue.co.kr{url}"
            content_elem = article.find('p') or article.find('div', class_='excerpt')
            content = content_elem.get_text(strip=True) if content_elem else title
            date_elem = article.find('time') or article.find('span', class_='date')
            date = DateUtils.parse_date_string(date_elem.get_text()) if date_elem else None
            img_url = ""
            img_elem = article.find('img')
            if img_elem:
                img_url = img_elem.get('src') or img_elem.get('data-src') or ""
                if img_url and not img_url.startswith('http'):
                    img_url = f"https://www.vogue.co.kr{img_url}"
            item = CrawledItem(
                title=title,
                content=content,
                url=url,
                date=date,
                platform=platform,
                metadata={'search_keyword': keyword}
            )
            if img_url:
                item.image_urls.append(img_url)
            items.append(item)
        except Exception as e:
            logger.error(f"Error parsing Vogue article: {e}")
    return items


async def parse_elle_search(
    soup: BeautifulSoup,
    platform: str,
    keyword: str
) -> List[CrawledItem]:
    """Elle 검색 결과 파싱"""
    items: List[CrawledItem] = []

    articles = soup.find_all('li', class_='search-item') or \
        soup.find_all('div', class_='article-list-item')

    for article in articles:
        try:
            title_elem = article.find('h3') or article.find('h2')
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            link_elem = title_elem.find('a')
            if not link_elem:
                continue

            url = link_elem.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://www.ellekorea.co.kr{url}"

            date_elem = article.find('span', class_='date') or article.find('time')
            date = DateUtils.parse_date_string(date_elem.get_text()) if date_elem else None

            content_elem = article.find('p', class_='excerpt')
            content = content_elem.get_text(strip=True) if content_elem else title

            item = CrawledItem(
                title=title,
                content=content,
                url=url,
                date=date,
                platform=platform,
                metadata={'search_keyword': keyword}
            )

            items.append(item)

        except Exception as e:
            logger.error(f"Error parsing Elle article: {e}")

    return items


async def parse_harpers_search(
    soup: BeautifulSoup,
    platform: str,
    keyword: str
) -> List[CrawledItem]:
    """Harper's Bazaar 검색 결과 파싱"""
    items: List[CrawledItem] = []

    articles = soup.find_all('article') or soup.find_all('div', class_='post-item')

    for article in articles:
        try:
            title_elem = article.find('h2') or article.find('h3')
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            link_elem = title_elem.find('a')
            if not link_elem:
                continue

            url = link_elem.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://www.harpersbazaar.co.kr{url}"

            date_elem = article.find('time') or article.find('span', class_='post-date')
            date = DateUtils.parse_date_string(date_elem.get_text()) if date_elem else None

            content_elem = article.find('div', class_='excerpt') or article.find('p')
            content = content_elem.get_text(strip=True) if content_elem else title

            item = CrawledItem(
                title=title,
                content=content,
                url=url,
                date=date,
                platform=platform,
                metadata={'search_keyword': keyword}
            )

            items.append(item)

        except Exception as e:
            logger.error(f"Error parsing Harper's Bazaar article: {e}")

    return items


async def parse_fashion_network_search(
    soup: BeautifulSoup,
    platform: str,
    keyword: str
) -> List[CrawledItem]:
    """Fashion Network 검색 결과 파싱"""
    items: List[CrawledItem] = []

    articles = soup.find_all('div', class_='news-summary') or \
        soup.find_all('article', class_='news-item')

    for article in articles:
        try:
            title_elem = article.find('h3') or article.find('h2')
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            link_elem = title_elem.find('a')
            if not link_elem:
                continue

            url = link_elem.get('href', '')

            date_elem = article.find('time') or article.find('span', class_='date')
            date = DateUtils.parse_date_string(date_elem.get_text()) if date_elem else None

            content_elem = article.find('p', class_='summary') or article.find('div', class_='excerpt')
            content = content_elem.get_text(strip=True) if content_elem else title

            item = CrawledItem(
                title=title,
                content=content,
                url=url,
                date=date,
                platform=platform,
                metadata={'search_keyword': keyword}
            )

            items.append(item)

        except Exception as e:
            logger.error(f"Error parsing Fashion Network article: {e}")

    return items
