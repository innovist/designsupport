"""
Settings admin/auth endpoints
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.encryption import encrypt_data, decrypt_data
from .settings_shared import (
    sessions,
    create_session_token,
    validate_session,
    ApiKeyRequest,
    TestConnectionRequest,
    SettingsResponse,
    _build_api_status,
    _apply_api_key
)

logger = get_logger(__name__)
router = APIRouter()


async def _test_gemini(api_key: str) -> Dict[str, Any]:
    from ai_clients.gemini_client import GeminiClient
    client = GeminiClient()
    success = await client.validate_key(api_key)
    return {"success": success, "error": None if success else "Gemini validation failed"}


async def _test_glm(api_key: str) -> Dict[str, Any]:
    from ai_clients.glm_client import GLMClient
    client = GLMClient()
    success = await client.validate_key(api_key)
    return {"success": success, "error": None if success else "GLM validation failed"}


async def _test_zimage(api_key: str) -> Dict[str, Any]:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.z-image.ai/health",
            headers={"Authorization": f"Bearer {api_key}"}
        ) as response:
            return {
                "success": response.status == 200,
                "error": None if response.status == 200 else f"HTTP {response.status}"
            }


async def _run_connection_test(service: str, api_key: str) -> Dict[str, Any]:
    if service == "gemini":
        return await _test_gemini(api_key)
    if service == "glm":
        return await _test_glm(api_key)
    if service == "zimage":
        return await _test_zimage(api_key)
    return {"success": False, "error": f"Service {service} not supported for connection test"}


def _build_export_payload(settings: Any) -> Dict[str, Any]:
    return {
        "apiKeys": {
            "gemini": settings.gemini_api_key[:10] + "..." if settings.gemini_api_key else None,
            "glm": settings.glm_api_key[:10] + "..." if settings.glm_api_key else None,
        },
        "system": {
            "maxConcurrentRequests": settings.max_concurrent_crawls,
            "requestTimeout": settings.generation_timeout_seconds,
            "defaultLanguage": settings.default_language,
            "defaultQuality": "high"
        },
        "exported_at": datetime.now().isoformat()
    }


def _apply_import_settings(settings: Any, sys_config: Dict[str, Any]) -> None:
    if "maxConcurrentRequests" in sys_config:
        settings.max_concurrent_crawls = sys_config["maxConcurrentRequests"]
    if "requestTimeout" in sys_config:
        settings.generation_timeout_seconds = sys_config["requestTimeout"]
    if "defaultLanguage" in sys_config:
        settings.default_language = sys_config["defaultLanguage"]


@router.post("/login")
async def login() -> Dict[str, Any]:
    token = create_session_token()
    sessions[token] = {
        "created": datetime.now(),
        "expires": datetime.now() + timedelta(hours=24)
    }
    return {
        "success": True,
        "token": token,
        "expires_in": 24 * 3600
    }


@router.post("/logout")
async def logout(token: str = Depends(validate_session)) -> Dict[str, Any]:
    if token in sessions:
        del sessions[token]
    return {"success": True, "message": "Logged out successfully"}


@router.get("/status")
async def get_api_status(token: str = Depends(validate_session)) -> Dict[str, Any]:
    settings = get_settings()
    status_map = _build_api_status(settings)
    return {
        "success": True,
        "status": status_map,
        "configured": sum(status_map.values()) >= 2
    }


@router.post("/test-connection")
async def test_api_connection(
    request: TestConnectionRequest,
    token: str = Depends(validate_session)
) -> SettingsResponse:
    service = request.service.lower()
    api_key = request.api_key

    try:
        result = await _run_connection_test(service, api_key)
    except Exception as exc:
        logger.error(f"API connection test failed for {service}: {exc}")
        result = {"success": False, "error": str(exc)}

    return SettingsResponse(
        success=result["success"],
        message="Connection successful" if result["success"] else f"Connection failed: {result.get('error', 'Unknown error')}",
        data={"status": result}
    )


@router.post("/save-api-key")
async def save_api_key(
    request: ApiKeyRequest,
    token: str = Depends(validate_session)
) -> SettingsResponse:
    service = request.service.lower()
    api_key = request.api_key
    settings = get_settings()

    _apply_api_key(settings, service, api_key)
    logger.info(f"API key saved for service: {service}")

    return SettingsResponse(
        success=True,
        message=f"API key saved for {service}"
    )


@router.get("/system-config")
async def get_system_config(token: str = Depends(validate_session)) -> Dict[str, Any]:
    settings = get_settings()
    config = {
        "maxConcurrentRequests": settings.max_concurrent_crawls,
        "requestTimeout": settings.generation_timeout_seconds,
        "defaultLanguage": settings.default_language,
        "defaultQuality": "high",
        "autoSaveResults": True,
        "gpuEnabled": settings.gpu_enabled,
        "availableModels": settings.get_available_models()
    }

    return {
        "success": True,
        "config": config
    }


@router.post("/system-config")
async def update_system_config(
    config: Dict[str, Any],
    token: str = Depends(validate_session)
) -> SettingsResponse:
    settings = get_settings()
    _apply_import_settings(settings, config)
    logger.info("System configuration updated")

    return SettingsResponse(
        success=True,
        message="System configuration updated"
    )


@router.post("/export")
async def export_settings(token: str = Depends(validate_session)) -> Dict[str, Any]:
    settings = get_settings()
    export_data = _build_export_payload(settings)
    encrypted = encrypt_data(json.dumps(export_data))

    return {
        "success": True,
        "data": encrypted,
        "filename": f"fashion-ai-settings-{datetime.now().strftime('%Y%m%d')}.fashion"
    }


@router.post("/import")
async def import_settings(
    encrypted_data: str,
    token: str = Depends(validate_session)
) -> SettingsResponse:
    try:
        decrypted = decrypt_data(encrypted_data)
        import_data = json.loads(decrypted)
        if "system" not in import_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid settings file"
            )

        settings = get_settings()
        _apply_import_settings(settings, import_data["system"])
        logger.info("Settings imported successfully")

        return SettingsResponse(
            success=True,
            message="Settings imported successfully"
        )
    except Exception as exc:
        logger.error(f"Failed to import settings: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to import settings: Invalid file or decryption failed"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
