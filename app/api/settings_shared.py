"""
Shared settings models and helpers
"""

import secrets
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

security = HTTPBearer()
sessions: Dict[str, Dict[str, Any]] = {}


class ApiKeyRequest(BaseModel):
    service: str = Field(..., description="API service name")
    api_key: str = Field(..., description="API key to save")


class TestConnectionRequest(BaseModel):
    service: str = Field(..., description="API service name")
    api_key: str = Field(..., description="API key to test")


class SettingsResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ApiKeysUpdate(BaseModel):
    gemini: Optional[str] = None
    glm: Optional[str] = None
    seedream: Optional[str] = None
    nano_banana: Optional[str] = None
    perplexity: Optional[str] = None


class CrawlerConfigUpdate(BaseModel):
    crawler_workers: Optional[int] = Field(default=None, ge=1, le=50)
    crawler_timeout: Optional[int] = Field(default=None, ge=5, le=600)
    searxng_api_url: Optional[str] = Field(default=None, max_length=2048)


class ModelsUpdate(BaseModel):
    gemini_text: Optional[str] = None
    glm_text: Optional[str] = None


class AIResearchConfig(BaseModel):
    """AI 조사 설정 모델"""
    enabled: bool = False
    models: Optional[Dict[str, bool]] = None
    perplexity_model: Optional[str] = "sonar"
    research_depth: Optional[str] = "standard"


class SettingsUpdate(BaseModel):
    api_keys: Optional[ApiKeysUpdate] = None
    config: Optional[CrawlerConfigUpdate] = None
    models: Optional[ModelsUpdate] = None


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def validate_session(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if token not in sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    if datetime.now() > sessions[token]["expires"]:
        del sessions[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    return token


def _build_api_status(settings: Any) -> Dict[str, bool]:
    return {
        "gemini": bool(settings.gemini_api_key and settings.gemini_api_key != "test-gemini-key"),
        "glm": bool(settings.glm_api_key and settings.glm_api_key != "test-glm-key"),
        "seedream": bool(settings.seedream_api_key),
        "nano_banana": bool(settings.nano_banana_api_key)
    }


def _validate_api_key(service: str, api_key: str) -> None:
    if service == "gemini" and not api_key.startswith("AIza"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Gemini API key format"
        )
    # GLM API key는 다양한 형식 가능 (길이만 검증)
    if service == "glm" and len(api_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GLM API key is too short"
        )


def _apply_api_key(settings: Any, service: str, api_key: str) -> None:
    _validate_api_key(service, api_key)
    attr_name = f"{service}_api_key"
    if service == "zimage":
        attr_name = "z_image_api_key"
    if hasattr(settings, attr_name):
        setattr(settings, attr_name, api_key)
