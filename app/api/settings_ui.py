"""
Settings UI endpoints
"""

from typing import Dict, Any

from fastapi import APIRouter

from app.core.config import get_settings
from app.core import settings_storage
from app.utils.system_detector import detect_gpu_availability
from .settings_shared import SettingsUpdate, _build_api_status, _apply_api_key

router = APIRouter()


def _get_api_status() -> Dict[str, bool]:
    """Build API status from stored settings"""
    stored = settings_storage.load_settings()
    api_keys = stored.get("api_keys", {})
    return {
        "gemini": bool(api_keys.get("gemini")),
        "glm": bool(api_keys.get("glm")),
        "seedream": bool(api_keys.get("seedream")),
        "nano_banana": bool(api_keys.get("nano_banana"))
    }


@router.get("/")
async def get_settings_overview() -> Dict[str, Any]:
    stored = settings_storage.load_settings()
    config = stored.get("config", {})
    models = stored.get("models", {})
    return {
        "status": _get_api_status(),
        "config": {
            "crawler_workers": config.get("crawler_workers", 5),
            "crawler_timeout": config.get("crawler_timeout", 30),
            "searxng_api_url": config.get("searxng_api_url")
        },
        "models": {
            "gemini_text": models.get("gemini_text", "gemini-2.5-flash"),
            "glm_text": models.get("glm_text", "glm-4.7")
        },
        "available_models": settings_storage.get_available_models()
    }


@router.get("/image-models")
async def get_image_model_status() -> Dict[str, Any]:
    settings = get_settings()
    if not settings.gpu_enabled:
        gpu_available = False
        gpu_info = "GPU disabled"
    else:
        gpu_available, gpu_info = detect_gpu_availability()

    zimage_available = bool(gpu_available)
    if not settings.z_image_api_key:
        zimage_available = False

    return {
        "gpu_available": bool(gpu_available),
        "gpu_info": gpu_info,
        "zimage_available": zimage_available
    }


@router.post("/")
async def update_settings(payload: SettingsUpdate) -> Dict[str, Any]:
    settings = get_settings()

    if payload.api_keys:
        api_keys = payload.api_keys.model_dump(exclude_none=True)
        for key_name, api_key in api_keys.items():
            if api_key:
                _apply_api_key(settings, key_name, api_key)
                settings_storage.save_api_key(key_name, api_key)
        settings_storage.clear_settings_cache()

    if payload.config:
        config = payload.config.model_dump(exclude_none=True)
        if "crawler_workers" in config:
            settings.max_concurrent_crawls = config["crawler_workers"]
        if "crawler_timeout" in config:
            settings.crawler_timeout_seconds = config["crawler_timeout"]
        if "searxng_api_url" in config:
            searxng_url = config["searxng_api_url"]
            if isinstance(searxng_url, str):
                searxng_url = searxng_url.strip()
            settings.searxng_api_url = searxng_url or None
            config["searxng_api_url"] = settings.searxng_api_url
        settings_storage.save_config(config)
        settings_storage.clear_settings_cache()

    if payload.models:
        models = payload.models.model_dump(exclude_none=True)
        gemini = models.get("gemini_text")
        glm = models.get("glm_text")
        if gemini or glm:
            settings_storage.save_model_settings(gemini, glm)
            settings_storage.clear_settings_cache()

    stored = settings_storage.load_settings()
    return {
        "success": True,
        "status": _get_api_status(),
        "config": settings_storage.get_config(),
        "models": stored.get("models", {})
    }
