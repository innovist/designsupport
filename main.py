"""
Fashion AI Generation System - Main Application Entry Point
Full-stack server with API and static file serving
"""

import uvicorn
import os
import sys
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.api.routes import router as api_router
from app.core.logging import get_logger
from app.core.config import get_settings
from app.core.database import init_db
from app.crawler_config import CRAWLER_CATEGORIES
from app.utils.searxng_runner import start_searxng, stop_searxng

logger = get_logger(__name__)
settings = get_settings()
SEARXNG_HOST = "127.0.0.1"
SEARXNG_PORT = 8913



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

    # Initialize database
    init_db()

    # Start SearXNG local instance if needed
    searxng_repo = project_root / "storage" / "searxng-src"
    searxng_settings = project_root / "storage" / "searxng"
    searxng_log = project_root / "logs" / "searxng.log"
    app.state.searxng_process = start_searxng(
        searxng_repo,
        searxng_settings,
        searxng_log,
        SEARXNG_HOST,
        SEARXNG_PORT,
        logger
    )

    yield

    logger.info("Shutting down Fashion AI Generation System...")
    stop_searxng(getattr(app.state, "searxng_process", None), logger)


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

# Templates
templates = Jinja2Templates(directory=str(project_root / "templates"))
templates.env.globals["now"] = datetime.now

# API routes - /api/v1 통일 (프론트엔드와 일치)
app.include_router(api_router, prefix="/api/v1")

# Page routes (Jinja2)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - Overview and quick actions"""
    return templates.TemplateResponse("pages/home.html", {"request": request})


@app.get("/projects", response_class=HTMLResponse)
async def projects(request: Request):
    """Projects management page - Create/manage projects and sessions"""
    return templates.TemplateResponse("pages/dashboard.html", {"request": request})


@app.get("/projects/new", response_class=HTMLResponse)
async def new_project(request: Request):
    """New project page"""
    return templates.TemplateResponse("pages/new_project.html", {"request": request})


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: int):
    """Project detail page"""
    return templates.TemplateResponse("pages/project_detail.html", {"request": request, "project_id": project_id})


@app.get("/projects/{project_id}/new-session", response_class=HTMLResponse)
async def new_session(request: Request, project_id: int):
    """New session page"""
    return templates.TemplateResponse(
        "pages/new_session.html",
        {"request": request, "project_id": project_id, "crawler_categories": CRAWLER_CATEGORIES}
    )


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_detail(request: Request, session_id: int):
    """Session detail page"""
    return templates.TemplateResponse("pages/session_detail.html", {"request": request, "session_id": session_id})


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """Sessions history page"""
    return templates.TemplateResponse("pages/history.html", {"request": request})


@app.get("/ideas", response_class=HTMLResponse)
async def ideas(request: Request):
    """Ideas page"""
    return templates.TemplateResponse("pages/ideas.html", {"request": request})


@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot(request: Request):
    """Chatbot page"""
    return templates.TemplateResponse("pages/chatbot.html", {"request": request})


@app.get("/library", response_class=HTMLResponse)
async def library_page(request: Request):
    """Library page - Generated images gallery"""
    return templates.TemplateResponse("pages/library.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    return templates.TemplateResponse("pages/settings.html", {"request": request})


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
