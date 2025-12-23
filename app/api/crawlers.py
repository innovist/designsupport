"""
Crawlers API endpoints for UI integration
"""

from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.crawler_config import CRAWLER_CATEGORIES, CRAWLER_METADATA, get_crawler_by_id
from app.core.logging import get_logger
from crawlers.crawler_service import CrawlerService
from crawlers.searxng_crawler import SearxngCrawler

logger = get_logger(__name__)
router = APIRouter()

crawler_service = CrawlerService()
crawler_service.register_crawler("searxng", SearxngCrawler())
_test_results: List[Dict[str, Any]] = []


def _record_test_result(result: Dict[str, Any]) -> None:
    _test_results.insert(0, result)
    if len(_test_results) > 200:
        _test_results.pop()


@router.get("/")
async def get_all_crawlers() -> List[Dict[str, Any]]:
    """전체 크롤러 목록 반환 (flat)"""
    from app.crawler_config import get_all_crawlers as get_crawlers_list
    return get_crawlers_list()


@router.get("/list")
async def list_crawlers() -> Dict[str, Any]:
    """카테고리별 크롤러 목록 반환"""
    from app.crawler_config import get_crawler_count
    return {
        "categorized": CRAWLER_CATEGORIES,
        "metadata": CRAWLER_METADATA,
        "counts": get_crawler_count()
    }


@router.get("/test-results")
async def get_test_results(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
    """크롤러 테스트 결과 조회"""
    return {
        "results": _test_results[:limit]
    }


@router.post("/test/{crawler_id}")
async def test_crawler(crawler_id: str, keyword: str = Query("패션 트렌드")) -> Dict[str, Any]:
    """단일 크롤러 테스트"""
    crawler = get_crawler_by_id(crawler_id)
    if not crawler:
        raise HTTPException(status_code=404, detail="Crawler not found")
    if not crawler.get("enabled", False):
        result = {
            "crawler_id": crawler_id,
            "status": "disabled",
            "posts_count": 0,
            "tested_at": datetime.utcnow().isoformat(),
            "error_message": "Crawler disabled"
        }
        _record_test_result(result)
        return {"result": result}

    try:
        items = await crawler_service.crawl_single(crawler_id, keyword)
        result = {
            "crawler_id": crawler_id,
            "status": "success",
            "posts_count": len(items),
            "tested_at": datetime.utcnow().isoformat()
        }
        _record_test_result(result)
        return {"result": result}
    except Exception as e:
        logger.error(f"Crawler test failed: {crawler_id}, error={e}")
        result = {
            "crawler_id": crawler_id,
            "status": "error",
            "posts_count": 0,
            "tested_at": datetime.utcnow().isoformat(),
            "error_message": str(e)
        }
        _record_test_result(result)
        return {"result": result}
