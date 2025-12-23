"""
Analysis API endpoints for Fashion AI Generation System
"""

import asyncio
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.analysis_service import AnalysisService
from app.core.config import get_settings
from crawlers.crawler_service import CrawlerService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize analysis service
analysis_service = AnalysisService()
crawler_service = CrawlerService()

# In-memory analysis job store (use DB/Redis in production)
analysis_jobs: Dict[str, Dict[str, Any]] = {}


class TrendAnalysisRequest(BaseModel):
    keywords: List[str] = Field(..., description="Keywords to analyze")
    time_range: str = Field(default="7d", description="Time range: 1d, 7d, 30d")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Analysis filters")


class TrendAnalysisResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None


@router.post("/analyze-trends", response_model=TrendAnalysisResponse)
async def analyze_trends(request: TrendAnalysisRequest):
    """Analyze fashion trends based on keywords"""
    try:
        if not request.keywords:
            raise HTTPException(status_code=400, detail="Keywords are required for analysis")

        settings = get_settings()
        filters = request.filters or {}
        analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"
        analysis_jobs[analysis_id] = {
            "status": "processing",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None,
            "crawl_job_id": None,
            "completed_at": None
        }

        # Resolve crawl sources and limits
        sources = filters.get("sources")
        if not sources:
            sources = crawler_service.get_available_crawlers()

        max_items = filters.get("max_items", settings.max_crawl_pages * 10)
        max_pages = max(1, int(max_items) // 10)

        # Start crawling
        crawl_job_id = await crawler_service.start_crawl(
            keywords=request.keywords,
            sources=sources,
            max_pages=max_pages
        )
        analysis_jobs[analysis_id]["crawl_job_id"] = crawl_job_id

        # Poll crawling status until completion or timeout
        timeout_seconds = settings.analysis_timeout_seconds
        poll_interval = 5
        elapsed = 0

        while elapsed < timeout_seconds:
            status = await crawler_service.get_crawl_status(crawl_job_id)
            analysis_jobs[analysis_id]["progress"] = min(90, status.get("progress", 0))

            if status.get("status") == "completed":
                break
            if status.get("status") == "failed":
                raise RuntimeError(status.get("error") or "Crawling failed")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        if analysis_jobs[analysis_id]["progress"] < 100 and status.get("status") != "completed":
            raise TimeoutError("Crawling timed out before completion")

        crawled_data = await crawler_service.get_crawl_results(crawl_job_id)

        analysis_result = await analysis_service.analyze_trends(
            raw_data=crawled_data,
            filters={
                "time_range": request.time_range,
                **filters
            },
            user_input=", ".join(request.keywords)
        )

        analysis_jobs[analysis_id]["status"] = "completed"
        analysis_jobs[analysis_id]["progress"] = 100
        analysis_jobs[analysis_id]["result"] = analysis_result
        analysis_jobs[analysis_id]["completed_at"] = datetime.utcnow().isoformat()

        return TrendAnalysisResponse(
            success=True,
            session_id=analysis_id,
            message="Trend analysis completed",
            data=analysis_result
        )

    except Exception as e:
        logger.error(f"Failed to start trend analysis: {str(e)}")
        if "analysis_id" in locals() and analysis_id in analysis_jobs:
            analysis_jobs[analysis_id]["status"] = "failed"
            analysis_jobs[analysis_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis-status/{session_id}")
async def get_analysis_status(session_id: str):
    """Get analysis status by session ID"""
    try:
        job = analysis_jobs.get(session_id)
        if not job:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "status": {
                "status": job["status"],
                "progress": job.get("progress", 0),
                "error": job.get("error")
            }
        }

    except Exception as e:
        logger.error(f"Failed to get analysis status: {str(e)}")
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/trend-results/{session_id}")
async def get_trend_results(session_id: str):
    """Get completed trend analysis results"""
    try:
        job = analysis_jobs.get(session_id)
        if not job:
            raise HTTPException(status_code=404, detail="Session not found")

        if job["status"] != "completed":
            return {
                "success": False,
                "message": "Analysis not completed yet",
                "status": job["status"],
                "progress": job.get("progress", 0)
            }

        return {
            "success": True,
            "results": job["result"],
            "completed_at": job.get("completed_at")
        }

    except Exception as e:
        logger.error(f"Failed to get trend results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-insight")
async def get_quick_insight(keywords: List[str]):
    """Get quick trend insight without full analysis"""
    raise HTTPException(
        status_code=501,
        detail="Quick insight is not implemented. Use /analysis/analyze-trends instead."
    )
