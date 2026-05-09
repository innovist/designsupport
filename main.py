"""
Design Creative Support System - Application Entry Point
"""

import sys
import time
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.api.pages import router as pages_router
from app.api.routes.workspace import router as workspace_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.assets import router as assets_router
from app.api.routes.trends import router as trends_router
from app.api.routes.references import router as references_router
from app.api.routes.concepts import router as concepts_router
from app.api.routes.abstraction import router as abstraction_router
from app.api.routes.generation import router as generation_router
from app.api.routes.specs import router as specs_router
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.logging import get_logger, log_api_request, setup_logging
from app.core.security import configure_cors

settings = get_settings()
setup_logging(level=settings.log_level)
logger = get_logger(__name__)


# @MX:ANCHOR: [AUTO] Application lifespan manager - startup/shutdown hooks
# @MX:REASON: High fan_in function called by FastAPI framework on every application lifecycle event. Initializes database, creates directories, and ensures default workspace exists.
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Design Creative Support System v%s", settings.app_version)

    for dir_path in ("uploads/sketches", "uploads/generated", "logs"):
        (project_root / dir_path).mkdir(parents=True, exist_ok=True)

    init_db()

    with SessionLocal() as db:
        from app.infrastructure.repositories.workspace_repository import WorkspaceRepository
        WorkspaceRepository(db).ensure_default_workspace()

    logger.info("System ready on %s:%d", settings.host, settings.port)
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evidence-based design ideation support system",
    lifespan=lifespan,
)

configure_cors(app)


# @MX:NOTE: [AUTO] HTTP middleware for request/response logging - skips static assets
@app.middleware("http")
async def _log_requests(request: Request, call_next):
    """Log every HTTP request and response to api.log."""
    t0 = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - t0) * 1000
    # Skip static assets to keep log clean
    if not request.url.path.startswith(("/static/", "/uploads/")):
        log_api_request(request.method, request.url.path, response.status_code, duration_ms)
    return response


static_path = project_root / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

uploads_path = project_root / "uploads"
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# HTML pages
app.include_router(pages_router)

# @MX:NOTE: [AUTO] All API routers registered with /api prefix - ensures consistent API path structure
_API_ROUTERS = [
    workspace_router,
    sessions_router,
    conversations_router,
    assets_router,
    trends_router,
    references_router,
    concepts_router,
    abstraction_router,
    generation_router,
    specs_router,
]
for r in _API_ROUTERS:
    app.include_router(r, prefix="/api")


# @MX:NOTE: [AUTO] Health check endpoint for monitoring and load balancer probes
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
