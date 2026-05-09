"""
Use-case: create or update a FeatureModelSetting for a given feature key.
"""

from sqlalchemy.orm import Session

from app.application.dtos.workspace_dtos import FeatureModelUpdate
from app.core.logging import get_logger
from app.infrastructure.repositories.workspace_repository import WorkspaceRepository
from app.models.workspace import FeatureModelSetting

logger = get_logger(__name__)


def update_feature_model(
    db: Session, feature_key: str, updates: FeatureModelUpdate
) -> FeatureModelSetting:
    logger.info("[WORKSPACE] update_feature_model key=%s provider=%s model=%s",
                feature_key, updates.provider, updates.model)
    repo = WorkspaceRepository(db)
    workspace = repo.ensure_default_workspace()
    setting = repo.upsert_feature_model(workspace.id, feature_key, updates.model_dump())
    logger.info("[WORKSPACE] feature_model saved key=%s id=%s", feature_key, setting.id)
    return setting
