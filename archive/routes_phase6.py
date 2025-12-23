"""
API Routes for Fashion AI Generation System
"""

from fastapi import APIRouter
from typing import Dict, Any

from .settings import router as settings_router
from .analysis import router as analysis_router
from .generation import router as generation_router
from .crawler import router as crawler_router
from .blueprint import router as blueprint_router
from .projects import router as projects_router
from .sessions import router as sessions_router

# 메인 라우터 생성
router = APIRouter()

# 서브 라우터 등록
router.include_router(settings_router, prefix="/settings", tags=["settings"])
router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
router.include_router(generation_router, prefix="/generation", tags=["generation"])
router.include_router(crawler_router, prefix="/crawler", tags=["crawler"])
router.include_router(blueprint_router, prefix="/blueprint", tags=["blueprint"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])


@router.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "message": "Fashion AI Generation System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "projects": "/api/v1/projects",
            "sessions": "/api/v1/sessions",
            "settings": "/api/v1/settings",
            "analysis": "/api/v1/analysis",
            "generation": "/api/v1/generation",
            "crawler": "/api/v1/crawler",
            "blueprint": "/api/v1/blueprint"
        }
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint - accessible via /api/v1/health"""
    return {
        "status": "healthy",
        "service": "fashion-ai-api",
        "version": "1.0.0"
    }