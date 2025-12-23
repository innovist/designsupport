"""
크롤러 설정 및 메타데이터
모든 크롤러 활성화 상태
"""

from typing import Dict, List, Any

CRAWLER_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "fashion": {
        "name": "패션 플랫폼",
        "icon": "👗",
        "crawlers": [
            {
                "id": "musinsa",
                "name": "무신사",
                "enabled": True,
                "module": "musinsa_crawler",
                "class": "MusinsaCrawler",
                "description": "한국 대표 온라인 패션 플랫폼"
            },
            {
                "id": "fashion_insta",
                "name": "인스타그램",
                "enabled": True,
                "module": "fashion_insta_crawler",
                "class": "FashionInstaCrawler",
                "description": "패션 인플루언서 및 브랜드"
            },
            {
                "id": "pinterest",
                "name": "핀터레스트",
                "enabled": True,
                "module": "pinterest_crawler",
                "class": "PinterestCrawler",
                "description": "패션 영감 및 스타일 보드"
            }
        ]
    },
    "community": {
        "name": "커뮤니티",
        "icon": "💬",
        "crawlers": [
            {
                "id": "dcinside",
                "name": "DC인사이드",
                "enabled": True,
                "module": "dcinside_crawler",
                "class": "DcinsideCrawler",
                "description": "국내 최대 커뮤니티"
            },
            {
                "id": "theqoo",
                "name": "더쿠",
                "enabled": True,
                "module": "theqoo_crawler",
                "class": "TheqooCrawler",
                "description": "여성 커뮤니티"
            },
            {
                "id": "fmkorea",
                "name": "FM코리아",
                "enabled": True,
                "module": "fmkorea_crawler",
                "class": "FmkoreaCrawler",
                "description": "종합 커뮤니티"
            },
            {
                "id": "clien",
                "name": "클리앙",
                "enabled": True,
                "module": "clien_crawler",
                "class": "ClienCrawler",
                "description": "IT/생활 커뮤니티"
            },
            {
                "id": "ruliweb",
                "name": "루리웹",
                "enabled": True,
                "module": "ruliweb_crawler",
                "class": "RuliwebCrawler",
                "description": "게임/서브컬처 커뮤니티"
            },
            {
                "id": "ppomppu",
                "name": "뽐뿌",
                "enabled": True,
                "module": "ppomppu_crawler",
                "class": "PpomppuCrawler",
                "description": "쇼핑/핫딜 커뮤니티"
            },
            {
                "id": "mlbpark",
                "name": "MLB파크",
                "enabled": True,
                "module": "mlbpark_crawler",
                "class": "MlbparkCrawler",
                "description": "스포츠 커뮤니티"
            },
            {
                "id": "blind",
                "name": "블라인드",
                "enabled": True,
                "module": "blind_crawler",
                "class": "BlindCrawler",
                "description": "직장인 익명 커뮤니티"
            },
            {
                "id": "etoland",
                "name": "에토랜드",
                "enabled": True,
                "module": "etoland_crawler",
                "class": "EtolandCrawler",
                "description": "종합 커뮤니티"
            },
            {
                "id": "inven",
                "name": "인벤",
                "enabled": True,
                "module": "inven_crawler",
                "class": "InvenCrawler",
                "description": "게임 커뮤니티"
            }
        ]
    },
    "portal": {
        "name": "포털/블로그",
        "icon": "🌐",
        "crawlers": [
            {
                "id": "naver_blog",
                "name": "네이버블로그",
                "enabled": True,
                "module": "naver_blog_crawler",
                "class": "NaverBlogCrawler",
                "description": "네이버 블로그 검색"
            },
            {
                "id": "naver_cafe",
                "name": "네이버카페",
                "enabled": True,
                "module": "naver_cafe_crawler",
                "class": "NaverCafeCrawler",
                "description": "네이버 카페 검색"
            },
            {
                "id": "daum_cafe",
                "name": "다음카페",
                "enabled": True,
                "module": "daum_cafe_crawler",
                "class": "DaumCafeCrawler",
                "description": "다음 카페 검색"
            }
        ]
    },
    "media": {
        "name": "미디어",
        "icon": "🎬",
        "crawlers": [
            {
                "id": "youtube",
                "name": "유튜브",
                "enabled": True,
                "module": "youtube_crawler",
                "class": "YoutubeCrawler",
                "description": "유튜브 영상 검색"
            }
        ]
    },
    "news": {
        "name": "뉴스/언론",
        "icon": "📰",
        "crawlers": [
            {
                "id": "fashion_news",
                "name": "패션N",
                "enabled": True,
                "module": "fashion_news_crawler",
                "class": "FashionNewsCrawler",
                "description": "패션 미디어 기사"
            },
            {
                "id": "wgsn",
                "name": "WGSN",
                "enabled": True,
                "module": "wgsn_crawler",
                "class": "WGSNCrawler",
                "description": "글로벌 패션 트렌드"
            },
            {
                "id": "natenews",
                "name": "네이트뉴스",
                "enabled": True,
                "module": "nate_news_crawler",
                "class": "NateNewsCrawler",
                "description": "종합 뉴스 검색"
            }
        ]
    },
    "search": {
        "name": "검색",
        "icon": "🔎",
        "crawlers": [
            {
                "id": "searxng",
                "name": "SearXNG",
                "enabled": True,
                "module": "searxng_crawler",
                "class": "SearxngCrawler",
                "description": "검색 엔진 결과 수집"
            }
        ]
    }
}


def get_all_crawlers() -> List[Dict[str, Any]]:
    """모든 크롤러 목록 반환"""
    all_crawlers = []
    for category_id, category_data in CRAWLER_CATEGORIES.items():
        for crawler in category_data["crawlers"]:
            crawler_copy = crawler.copy()
            crawler_copy["category"] = category_id
            crawler_copy["category_name"] = category_data["name"]
            crawler_copy["category_icon"] = category_data["icon"]
            all_crawlers.append(crawler_copy)
    return all_crawlers


def get_crawlers_by_category(category: str) -> List[Dict[str, Any]]:
    """특정 카테고리의 크롤러 목록 반환"""
    if category not in CRAWLER_CATEGORIES:
        return []
    return CRAWLER_CATEGORIES[category]["crawlers"]


def get_enabled_crawlers() -> List[Dict[str, Any]]:
    """활성화된 크롤러만 반환"""
    return [c for c in get_all_crawlers() if c.get("enabled", False)]


def get_crawler_by_id(crawler_id: str) -> Dict[str, Any] | None:
    """ID로 크롤러 조회"""
    for crawler in get_all_crawlers():
        if crawler["id"] == crawler_id:
            return crawler
    return None


def get_crawler_count() -> Dict[str, int]:
    """카테고리별 크롤러 개수"""
    counts = {category_id: len(category_data["crawlers"])
              for category_id, category_data in CRAWLER_CATEGORIES.items()}
    counts["total"] = sum(counts.values())
    counts["enabled"] = len(get_enabled_crawlers())
    return counts


def get_crawler_ids() -> List[str]:
    """모든 크롤러 ID 목록 반환"""
    return [c["id"] for c in get_all_crawlers()]


CRAWLER_METADATA = {
    "total_count": len(get_all_crawlers()),
    "categories": list(CRAWLER_CATEGORIES.keys()),
    "category_names": [cat["name"] for cat in CRAWLER_CATEGORIES.values()],
    "enabled_count": len(get_enabled_crawlers()),
    "crawler_ids": get_crawler_ids()
}
