"""
Settings router aggregator
"""

from fastapi import APIRouter

from .settings_ui import router as ui_router
from .settings_admin import router as admin_router

router = APIRouter()
router.include_router(ui_router)
router.include_router(admin_router)
