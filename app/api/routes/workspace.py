"""
Workspace settings API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errors import validation_error_response
from app.application.dtos.workspace_dtos import (
    FeatureModelResponse,
    FeatureModelUpdate,
    TrendSettingResponse,
    TrendSettingUpdate,
    WorkspaceSettingResponse,
    WorkspaceSettingUpdate,
)
from app.application.use_cases.workspace.get_workspace_settings import (
    get_api_key_aliases,
    get_workspace_settings,
)
from app.application.use_cases.workspace.update_feature_model import update_feature_model
from app.application.use_cases.workspace.update_workspace_settings import (
    update_trend_settings,
    update_workspace_settings,
)
from app.core.database import get_db

router = APIRouter(tags=["workspace"])


@router.get("/workspace/settings", response_model=WorkspaceSettingResponse)
def api_get_workspace_settings(db: Session = Depends(get_db)):
    data = get_workspace_settings(db)
    setting = data["setting"]
    if not setting:
        return validation_error_response("No workspace settings found")
    return setting


@router.put("/workspace/settings", response_model=WorkspaceSettingResponse)
def api_update_workspace_settings(
    updates: WorkspaceSettingUpdate, db: Session = Depends(get_db)
):
    return update_workspace_settings(db, updates)


@router.get("/workspace/feature-models", response_model=list[FeatureModelResponse])
def api_list_feature_models(db: Session = Depends(get_db)):
    data = get_workspace_settings(db)
    return data["feature_models"]


@router.put("/workspace/feature-models/{feature_key}", response_model=FeatureModelResponse)
def api_update_feature_model(
    feature_key: str, updates: FeatureModelUpdate, db: Session = Depends(get_db)
):
    return update_feature_model(db, feature_key, updates)


@router.post("/workspace/feature-models/{feature_key}/connection-test")
async def api_test_feature_model_connection(
    feature_key: str, db: Session = Depends(get_db)
):
    from app.application.ports.ai_client import AIMessage
    from app.infrastructure.ai_clients.factory import SettingsRequiredError, get_ai_client

    try:
        client = await get_ai_client(db, feature_key)
        provider = getattr(client, "provider", None) or client.__class__.__name__
        model = getattr(client, "model", None) or getattr(client, "_model", None)
        if feature_key == "image_generation":
            return {
                "ok": True,
                "provider": provider,
                "model": model,
                "message": "이미지 생성 모델 설정을 확인했습니다. 실제 API 호출은 이미지 생성 시 검증됩니다.",
            }
        response = await client.complete(
            [AIMessage(role="user", content="Reply with OK only.")],
            temperature=0,
            max_tokens=8,
        )
        return {
            "ok": bool(response.content.strip()),
            "provider": response.provider,
            "model": response.model,
            "message": "연결 확인 완료",
        }
    except SettingsRequiredError as exc:
        return validation_error_response(str(exc))
    except Exception as exc:
        return validation_error_response(f"연결 확인 실패: {exc}")


@router.get("/workspace/trend-settings", response_model=TrendSettingResponse)
def api_get_trend_settings(db: Session = Depends(get_db)):
    data = get_workspace_settings(db)
    setting = data["trend_setting"]
    if not setting:
        from app.infrastructure.repositories.workspace_repository import WorkspaceRepository
        workspace = WorkspaceRepository(db).ensure_default_workspace()
        from app.models.workspace import WorkspaceTrendSetting
        setting = WorkspaceTrendSetting(workspace_id=workspace.id)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.put("/workspace/trend-settings", response_model=TrendSettingResponse)
def api_update_trend_settings(
    updates: TrendSettingUpdate, db: Session = Depends(get_db)
):
    return update_trend_settings(db, updates)


@router.get("/workspace/api-key-aliases")
def api_get_key_aliases():
    return {"configured_providers": get_api_key_aliases()}


# Full model catalog per provider — used by settings UI
# Model IDs match .env model comparison table (2026-05-05).
# "-non" variants share the same API model_id but disable thinking mode (factory handles this).
_MODEL_CATALOG = {
    "openai": {
        "label": "OpenAI",
        "models": [
            {"id": "gpt-5.4",       "label": "GPT-5.4",       "types": ["text", "multimodal"]},
            {"id": "gpt-5.4-mini",  "label": "GPT-5.4 mini",  "types": ["text", "multimodal"]},
            {"id": "gpt-5.4-nano",  "label": "GPT-5.4 nano",  "types": ["text", "multimodal"]},
            {"id": "gpt-image-1",   "label": "GPT Image-1",   "types": ["image"]},
        ],
    },
    "gemini": {
        "label": "Google Gemini",
        "models": [
            {"id": "gemini-3.1-pro-preview",        "label": "Gemini 3.1 Pro",              "types": ["text", "multimodal"]},
            {"id": "gemini-3-flash-preview",         "label": "Gemini 3 Flash",              "types": ["text", "multimodal"]},
            {"id": "gemini-3.1-flash-lite",          "label": "Gemini 3.1 Flash Lite",       "types": ["text", "multimodal"]},
            {"id": "gemini-3.1-flash-image-preview", "label": "Gemini 3.1 Flash Image",      "types": ["image"]},
            {"id": "gemini-3-pro-image-preview",     "label": "Gemini 3 Pro Image",          "types": ["image"]},
            {"id": "gemini-2.5-flash-image",         "label": "Gemini 2.5 Flash Image",      "types": ["image"]},
        ],
    },
    "deepseek": {
        "label": "DeepSeek",
        "models": [
            {"id": "deepseek-chat",     "label": "DeepSeek v3.2 Chat",  "types": ["text"]},
            {"id": "deepseek-v4-pro",   "label": "DeepSeek V4 Pro",     "types": ["text"]},
            {"id": "deepseek-v4-flash", "label": "DeepSeek V4 Flash",   "types": ["text"]},
        ],
    },
    "alibaba": {
        "label": "Alibaba (Qwen)",
        "models": [
            {"id": "qwen3.6-flash",       "label": "Qwen 3.6 Flash",               "types": ["text", "multimodal"]},
            {"id": "qwen3.6-Flash-non",   "label": "Qwen 3.6 Flash (no think)",    "types": ["text", "multimodal"]},
            {"id": "qwen3.6-max-preview", "label": "Qwen 3.6 Max",                 "types": ["text", "multimodal"]},
            {"id": "qwen3.6-Max-non",     "label": "Qwen 3.6 Max (no think)",      "types": ["text", "multimodal"]},
            {"id": "qwen3.6-plus",        "label": "Qwen 3.6 Plus",                "types": ["text", "multimodal"]},
            {"id": "qwen3.6-Plus-Non",    "label": "Qwen 3.6 Plus (no think)",     "types": ["text", "multimodal"]},
            {"id": "qwen-plus",           "label": "Qwen 3.5 Plus",                "types": ["text", "multimodal"]},
            {"id": "qwen3.5-flash",       "label": "Qwen 3.5 Flash",               "types": ["text", "multimodal"]},
            {"id": "z-image-turbo",       "label": "Z Image Turbo (Standard)",      "types": ["image"]},
            {"id": "z-image-turbo-think", "label": "Z Image Turbo (Think +prompt)", "types": ["image"]},
        ],
    },
    "xiaomi": {
        "label": "Xiaomi Mimo",
        "models": [
            {"id": "mimo-v2.5-pro",     "label": "Mimo v2.5 Pro",            "types": ["text"]},
            {"id": "mimo-v2.5-pro-non", "label": "Mimo v2.5 Pro (no think)", "types": ["text"]},
            {"id": "mimo-v2.5",         "label": "Mimo v2.5",                "types": ["text", "multimodal"]},
            {"id": "mimo-v2.5-non",     "label": "Mimo v2.5 (no think)",     "types": ["text", "multimodal"]},
            {"id": "mimo-v2-pro",       "label": "Mimo v2 Pro",              "types": ["text"]},
            {"id": "mimo-v2-omni",      "label": "Mimo v2 Omni",             "types": ["text", "multimodal"]},
            {"id": "mimo-v2-flash",     "label": "Mimo v2 Flash",            "types": ["text"]},
        ],
    },
    "minimax": {
        "label": "Minimax",
        "models": [
            {"id": "MiniMax-M2.7",           "label": "MiniMax M2.7",           "types": ["text"]},
            {"id": "MiniMax-M2.7-highspeed", "label": "MiniMax M2.7 Highspeed", "types": ["text"]},
        ],
    },
    "kimi": {
        "label": "Kimi (Moonshot)",
        "models": [
            {"id": "kimi-k2.6",     "label": "Kimi K2.6",            "types": ["text", "multimodal"]},
            {"id": "kimi-k2.6-non", "label": "Kimi K2.6 (no think)", "types": ["text", "multimodal"]},
            {"id": "kimi-k2.5",     "label": "Kimi K2.5",            "types": ["text", "multimodal"]},
            {"id": "kimi-k2.5-non", "label": "Kimi K2.5 (no think)", "types": ["text", "multimodal"]},
        ],
    },
    "seedream": {
        "label": "Seedream (ByteDance)",
        "models": [
            {"id": "seedream-5-0-260128",  "label": "Seedream 5.0", "types": ["image"]},
            {"id": "seedream-4-5-251128",  "label": "Seedream 4.5", "types": ["image"]},
            {"id": "seedream-4-0-250828",  "label": "Seedream 4.0", "types": ["image"]},
        ],
    },
}


@router.get("/workspace/available-models")
def api_get_available_models():
    """Return model catalog filtered to configured providers."""
    from app.core.config import get_settings
    configured = get_settings().available_providers()
    result = {}
    for provider, info in _MODEL_CATALOG.items():
        result[provider] = {
            **info,
            "configured": provider in configured,
        }
    return result
