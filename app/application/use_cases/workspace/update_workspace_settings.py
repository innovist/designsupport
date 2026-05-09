"""
Use-case: update workspace general settings and trend settings.
"""

from sqlalchemy.orm import Session

from app.application.dtos.workspace_dtos import TrendSettingUpdate, WorkspaceSettingUpdate
from app.core.logging import get_logger
from app.infrastructure.repositories.workspace_repository import WorkspaceRepository
from app.models.workspace import WorkspaceSetting, WorkspaceTrendSetting

logger = get_logger(__name__)


def update_workspace_settings(
    db: Session, updates: WorkspaceSettingUpdate
) -> WorkspaceSetting:
    logger.info("[WORKSPACE] updating settings fields=%s", list(updates.model_dump(exclude_none=True).keys()))
    repo = WorkspaceRepository(db)
    workspace = repo.ensure_default_workspace()
    setting = repo.upsert_setting(workspace.id, updates.model_dump(exclude_none=True))
    logger.info("[WORKSPACE] settings updated workspace=%s", workspace.id)
    return setting


def update_trend_settings(
    db: Session, updates: TrendSettingUpdate
) -> WorkspaceTrendSetting:
    logger.info("[WORKSPACE] updating trend settings fields=%s", list(updates.model_dump(exclude_none=True).keys()))
    repo = WorkspaceRepository(db)
    workspace = repo.ensure_default_workspace()
    trend_setting = repo.upsert_trend_setting(workspace.id, updates.model_dump(exclude_none=True))
    logger.info("[WORKSPACE] trend settings updated workspace=%s", workspace.id)
    return trend_setting
