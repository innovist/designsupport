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
        if feature_key in {"image_generation", "sketch_generation", "final_image_generation"}:
            return {
                "ok": True,
                "provider": provider,
                "model": model,
                "message": "이미지 모델 설정을 확인했습니다. 실제 API 호출은 생성 실행 시 검증됩니다.",
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


@router.get("/workspace/available-models")
def api_get_available_models():
    """Return model catalog filtered to configured providers."""
    from app.core.config import get_settings
    from app.core.model_catalog import MODEL_CATALOG
    configured = get_settings().available_providers()
    result = {}
    for provider, info in MODEL_CATALOG.items():
        result[provider] = {
            **info,
            "configured": provider in configured,
        }
    return result


@router.get("/workspace/search-backend")
def api_get_search_backend():
    """Return current search backend configuration."""
    from app.core.config import get_settings
    s = get_settings()
    return {
        "search_backend": s.search_backend,
        "web_search_crawler_api_base_url": s.web_search_crawler_api_base_url or "",
        "web_search_crawler_api_token": "***" if s.web_search_crawler_api_token else "",
        "searxng_api_url": s.searxng_api_url or "",
        "crawl4ai_api_url": s.crawl4ai_api_url or "",
    }


@router.put("/workspace/search-backend")
async def api_update_search_backend(updates: dict):
    """Update search backend settings in .env file."""
    from pathlib import Path

    env_path = Path(".env")
    if not env_path.exists():
        return {"ok": False, "detail": ".env 파일이 없습니다."}

    lines = env_path.read_text(encoding="utf-8").splitlines()
    keys_to_update = {
        "search_backend": "SEARCH_BACKEND",
        "web_search_crawler_api_base_url": "WEB_SEARCH_CRAWLER_API_BASE_URL",
        "web_search_crawler_api_token": "WEB_SEARCH_CRAWLER_API_TOKEN",
        "searxng_api_url": "SEARXNG_API_URL",
        "crawl4ai_api_url": "CRAWL4AI_API_URL",
    }

    existing_keys = {line.split("=")[0].strip() for line in lines if "=" in line and not line.strip().startswith("#")}

    for field, env_key in keys_to_update.items():
        if field not in updates:
            continue
        value = updates[field]
        if value is None:
            value = ""
        env_line = f"{env_key}={value}"

        if env_key in existing_keys:
            lines = [
                env_line if line.split("=")[0].strip() == env_key else line
                for line in lines
            ]
        else:
            lines.append(env_line)

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Update the cached settings
    from app.core.config import Settings, get_settings
    get_settings.cache_clear()
    new_settings = Settings()
    import app.core.config as cfg_mod
    cfg_mod.settings = new_settings

    return {"ok": True, "search_backend": updates.get("search_backend", "none")}


@router.post("/workspace/search-backend/test")
async def api_test_search_backend():
    """Test the current search backend connectivity."""
    from app.infrastructure.search.web_search import get_search_client

    client = get_search_client()
    try:
        results = await client.web_search("test query design trends", num_results=3)
        return {
            "ok": True,
            "message": f"연결 확인 완료 ({len(results)}건 결과 반환)",
            "result_count": len(results),
        }
    except Exception as exc:
        return {"ok": False, "message": f"연결 실패: {exc}"}
