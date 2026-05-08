"""
Crawl step utilities for the pipeline
"""

# @MX:NOTE: [AUTO] Crawl utilities - helper functions for crawler configuration and progress tracking
# Provides filter formatting, crawl planning, and progress computation for the pipeline

from datetime import datetime
from typing import List, Dict, Any, Optional

from crawlers.crawler_service import CrawlerService
from crawlers.base_crawler import CrawledItem

FILTER_VALUE_MAP = {
    "gender": {
        "female": "여성",
        "male": "남성",
        "unisex": "유니섹스"
    },
    "season": {
        "spring": "봄",
        "summer": "여름",
        "fall": "가을",
        "winter": "겨울"
    },
    "age": {
        "toddler": "유아(0-5세)",
        "child": "아동(6-12세)",
        "teen": "청소년(13-19세)",
        "20s": "20대",
        "30s": "30대",
        "40s": "40대",
        "50s_plus": "50대+"
    },
    "category": {
        # 스타일
        "casual": "캐주얼",
        "formal": "포멀",
        "sports": "스포츠",
        "outdoor": "아웃도어",
        "street": "스트릿",
        "minimal": "미니멀",
        "vintage": "빈티지",
        "romantic": "로맨틱",
        "ethnic": "에스닉",
        "avantgarde": "아방가르드",
        "genderless": "젠더리스",
        # 의류 종류
        "top": "상의",
        "bottom": "하의",
        "dress": "원피스",
        "outer": "아우터",
        "underwear": "내의",
        "sleepwear": "수면복",
        "swimwear": "수영복",
        "activewear": "액티브웨어"
    }
}


def format_filters(filters: Dict[str, Any]) -> str:
    if not filters:
        return "none"
    def to_text(key: str, value: Any) -> str:
        if value is None:
            return ""
        label_map = FILTER_VALUE_MAP.get(key, {})
        if isinstance(value, list):
            return ", ".join([label_map.get(v, str(v)) for v in value if v is not None])
        return label_map.get(value, str(value))
    parts = []
    for key, label in (("gender", "gender"), ("age", "age"), ("season", "season"), ("category", "category")):
        text = to_text(key, filters.get(key))
        if text:
            parts.append(f"{label}: {text}")
    return "; ".join(parts) if parts else "none"


def parse_date_value(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def estimate_expected_items(
    sources: List[str],
    keyword_count: int,
    max_items: int,
    youtube_config: Dict[str, Any]
) -> int:
    if keyword_count <= 0:
        return 0
    expected = 0
    for source in sources:
        if source == "youtube":
            keyword_max = youtube_config.get("keyword_max") or max_items
            channel_urls = youtube_config.get("channel_urls") or []
            channel_max = youtube_config.get("channel_max")
            if channel_urls:
                per_channel = channel_max if channel_max is not None else max(1, max_items // len(channel_urls))
                expected += keyword_count * (keyword_max + (per_channel * len(channel_urls)))
            else:
                expected += keyword_count * keyword_max
        else:
            expected += keyword_count * max_items
    return expected


def build_crawl_plan(
    crawler_config: Dict[str, Any],
    default_sources: List[str]
) -> tuple[List[str], int, Dict[str, Any], Optional[datetime], Optional[datetime]]:
    sources = crawler_config.get("crawlers") or list(default_sources)
    max_items = max(1, int(crawler_config.get("max_items_per_source", 100)))
    enable_stt = crawler_config.get("youtube_enable_stt")
    if enable_stt is None:
        enable_stt = True
    youtube_config = {
        "channel_urls": crawler_config.get("youtube_channel_urls", []),
        "keyword_max": crawler_config.get("youtube_keyword_count"),
        "channel_max": crawler_config.get("youtube_channel_max"),
        "parallel": crawler_config.get("youtube_parallel"),
        "enable_stt": enable_stt
    }
    start_date = parse_date_value(crawler_config.get("start_date"))
    end_date = parse_date_value(crawler_config.get("end_date"))
    return sources, max_items, youtube_config, start_date, end_date


def build_source_counts_text(items: List[CrawledItem], sources: List[str]) -> str:
    counts = {source: 0 for source in sources}
    for item in items:
        counts[item.source] = counts.get(item.source, 0) + 1
    return ", ".join([f"{key}:{value}" for key, value in counts.items()])

def build_youtube_hint(sources: List[str], youtube_config: Dict[str, Any]) -> str:
    if "youtube" not in sources:
        return ""
    yt_parts = []
    keyword_max = youtube_config.get("keyword_max")
    if keyword_max:
        yt_parts.append(f"YT키워드:{keyword_max}")
    channel_urls = youtube_config.get("channel_urls") or []
    channel_max = youtube_config.get("channel_max")
    if channel_max and channel_urls:
        yt_parts.append(f"YT채널:{channel_max}x{len(channel_urls)}")
    return f", {' '.join(yt_parts)}" if yt_parts else ""


def build_crawl_start_message(
    sources: List[str],
    total_keywords: int,
    expected_items: int,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    max_items: int,
    youtube_config: Dict[str, Any]
) -> str:
    period = f"{start_date.date() if start_date else '-'}~{end_date.date() if end_date else '-'}"
    youtube_hint = build_youtube_hint(sources, youtube_config)
    return (
        f"데이터 수집 시작 (소스: {', '.join(sources)}, 키워드:{total_keywords}, 예상:{expected_items}, "
        f"기간: {period}, 소스당:{max_items}{youtube_hint})"
    )


def format_crawler_errors(errors: Dict[str, str], limit: int = 160) -> str:
    if not errors:
        return ""
    summary = "; ".join([f"{key}:{value}" for key, value in errors.items()])
    if len(summary) > limit:
        summary = summary[:limit] + "..."
    return f", 오류: {summary}"


def compute_crawl_progress(
    collected: int,
    expected: int,
    keyword_index: int,
    total_keywords: int,
    base: float = 25.0,
    span: float = 25.0
) -> float:
    total_divisor = max(total_keywords, 1)
    keyword_ratio = keyword_index / total_divisor
    ratio = keyword_ratio
    if expected > 0:
        ratio = max(collected / expected, keyword_ratio)
    return base + min(1.0, ratio) * span


def apply_crawler_config(
    crawler_service: CrawlerService,
    sources: List[str],
    max_items: int,
    youtube_config: Dict[str, Any]
) -> None:
    for source in sources:
        crawler = crawler_service.crawlers.get(source)
        if crawler and hasattr(crawler, "max_items"):
            crawler.max_items = max_items
    youtube = crawler_service.crawlers.get("youtube")
    if "youtube" in sources and youtube and hasattr(youtube, "apply_config"):
        youtube.apply_config(
            enable_stt=youtube_config.get("enable_stt"),
            max_workers=youtube_config.get("parallel"),
            channel_urls=youtube_config.get("channel_urls"),
            keyword_max_items=youtube_config.get("keyword_max"),
            channel_max_items=youtube_config.get("channel_max"),
            max_items=max_items
        )
    elif "youtube" in sources and youtube:
        youtube.max_items = max_items
        if youtube_config.get("channel_urls") is not None:
            youtube.channel_urls = youtube_config.get("channel_urls") or []


def serialize_crawled_items(items: List[CrawledItem]) -> List[Dict[str, Any]]:
    results = []
    for item in items:
        if not item:
            continue
        results.append({
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
    return results
