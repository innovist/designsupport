"""
Crawler API endpoints for Fashion AI Generation System
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from crawlers.crawler_service import CrawlerService
from app.crawler_config import get_enabled_crawlers, get_all_crawlers
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize crawler service
crawler_service = CrawlerService()


class CrawlerRequest(BaseModel):
    sources: List[str] = Field(..., description="Data sources to crawl")
    keywords: List[str] = Field(..., description="Keywords to search for")
    max_items: int = Field(default=100, ge=10, le=1000, description="Maximum items to collect")


class CrawlerResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    message: str
    estimated_time: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


@router.post("/start", response_model=CrawlerResponse)
async def start_crawling(
    request: CrawlerRequest,
    background_tasks: BackgroundTasks
):
    """Start data crawling from specified sources"""
    try:
        # Validate sources - 활성화된 크롤러만 허용
        valid_sources = [c["id"] for c in get_enabled_crawlers()]

        invalid_sources = [s for s in request.sources if s not in valid_sources]
        if invalid_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sources: {', '.join(invalid_sources)}. Valid: {', '.join(valid_sources)}"
            )

        # Start crawling job
        job_id = await crawler_service.start_crawl(
            keywords=request.keywords,
            sources=request.sources,
            max_pages=request.max_items // 10  # Rough estimation
        )

        # Estimate time (5 seconds per item)
        estimated_time = min(request.max_items * 5, 600)  # Max 10 minutes

        return CrawlerResponse(
            success=True,
            job_id=job_id,
            message="Crawling started successfully",
            estimated_time=estimated_time,
            data={"job_id": job_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start crawling: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
async def get_crawl_status(job_id: str):
    """Get crawling job status"""
    try:
        status = await crawler_service.get_crawl_status(job_id)
        return {
            "success": True,
            "message": "Status retrieved",
            "data": {
                "job_id": job_id,
                "status": status.get("status"),
                "progress": status.get("progress", 0),
                "items_collected": status.get("items_collected", 0),
                "error": status.get("error")
            }
        }

    except Exception as e:
        logger.error(f"Failed to get crawl status: {str(e)}")
        raise HTTPException(status_code=404, detail="Job not found")


@router.get("/results/{job_id}")
async def get_crawl_results(
    job_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get crawling results"""
    try:
        # Check if job is completed
        status = await crawler_service.get_crawl_status(job_id)
        if status.get("status") != "completed":
            return {
                "success": False,
                "message": "Job not completed yet",
                "data": {
                    "status": status.get("status"),
                    "progress": status.get("progress", 0)
                }
            }

        # Get results
        results = await crawler_service.get_crawl_results(job_id)

        # Apply pagination
        total = len(results)
        paginated_results = results[offset:offset + limit]

        # Format results
        formatted_results = []
        for item in paginated_results:
            formatted_results.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "content": item.get("content", "")[:500] + "...",
                "source": item.get("source"),
                "url": item.get("url"),
                "published_at": item.get("published_at"),
                "keywords": item.get("keywords", [])
            })

        return {
            "success": True,
            "message": "Results retrieved",
            "data": {
                "items": formatted_results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }

    except Exception as e:
        logger.error(f"Failed to get crawl results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def get_available_sources():
    """Get list of available data sources"""
    return {
        "success": True,
        "data": {
            "sources": get_all_crawlers()
        }
    }


@router.delete("/job/{job_id}")
async def cancel_crawl_job(job_id: str):
    """Cancel a crawling job"""
    try:
        # Check if job exists
        status = await crawler_service.get_crawl_status(job_id)
        if status.get("status") in ["completed", "failed", "cancelled"]:
            return {
                "success": False,
                "message": f"Job already {status.get('status')}"
            }

        # Cancel job
        # Note: Actual cancellation implementation needed
        await crawler_service.cancel_crawl(job_id)

        return {
            "success": True,
            "message": "Job cancelled successfully",
            "data": {"job_id": job_id}
        }

    except Exception as e:
        logger.error(f"Failed to cancel job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_crawl_stats():
    """Get crawling statistics"""
    try:
        stats = await crawler_service.get_crawler_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
