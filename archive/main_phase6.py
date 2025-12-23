"""
Fashion AI Generation System - Main Application Entry Point
Full-stack server with API and static file serving
"""

import uvicorn
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.api.routes import router as api_router
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Fashion AI Generation System...")

    # Check GPU availability
    from app.utils.system_detector import detect_gpu_availability
    has_gpu, gpu_type = detect_gpu_availability()
    logger.info(f"GPU Available: {has_gpu}, Type: {gpu_type}")

    # Initialize storage directories
    storage_dirs = [
        "storage/references",
        "storage/results",
        "storage/temp",
        "logs"
    ]

    for dir_path in storage_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directory ready: {full_path}")

    yield

    logger.info("Shutting down Fashion AI Generation System...")


# Create FastAPI application
app = FastAPI(
    title="Fashion AI Generation System",
    description="AI-powered fashion trend analysis and design generation system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = project_root / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# API routes - /api/v1 통일 (프론트엔드와 일치)
app.include_router(api_router, prefix="/api/v1")

# Root endpoint - serve index.html
@app.get("/")
async def root():
    """Serve main application"""
    index_path = static_path / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=content)
    return {"message": "Fashion AI Generation System API"}


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fashion-ai-system",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )