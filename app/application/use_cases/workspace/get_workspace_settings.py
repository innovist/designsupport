"""
Use-case: retrieve workspace settings and feature model settings.
"""

from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_workspace_settings(db: Session) -> dict:
    """Return the default workspace with all its settings."""
    from app.infrastructure.repositories.workspace_repository import WorkspaceRepository
    repo = WorkspaceRepository(db)
    workspace = repo.ensure_default_workspace()
    setting = repo.get_setting(workspace.id)
    feature_models = repo.list_feature_models(workspace.id)
    trend_setting = repo.get_trend_setting(workspace.id)
    logger.info("[WORKSPACE] settings loaded workspace=%s feature_models=%d", workspace.id, len(feature_models))
    return {
        "workspace": workspace,
        "setting": setting,
        "feature_models": feature_models,
        "trend_setting": trend_setting,
    }


def get_api_key_aliases() -> list[str]:
    """Return provider names that have API keys configured (not the keys themselves)."""
    from app.core.config import get_settings
    providers = get_settings().available_providers()
    logger.info("[WORKSPACE] api_key_aliases configured_providers=%s", providers)
    return providers
