"""
Repository for Workspace and related settings.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.workspace import (
    FeatureModelSetting,
    Workspace,
    WorkspaceSetting,
    WorkspaceTrendSetting,
)

# @MX:NOTE: [AUTO] Default AI model configuration per feature - fallback when workspace not configured
DEFAULT_FEATURE_MODELS = {
    "abstraction": ("openai", "gpt-4o-mini", 0.4, 2000),
    "sketch_analysis": ("openai", "gpt-4o", 0.3, 1200),
    "concept_generation": ("openai", "gpt-4o-mini", 0.7, 2000),
    "chat": ("openai", "gpt-4o-mini", 0.7, 2000),
    "image_generation": ("openai", "gpt-image-1", 0.7, 2000),
    "reference_analysis": ("openai", "gpt-4o-mini", 0.3, 1200),
    "brief_structuring": ("openai", "gpt-4o-mini", 0.3, 1000),
    "spec_writing": ("openai", "gpt-4o-mini", 0.3, 3000),
    "trend_analysis": ("openai", "gpt-4o-mini", 0.3, 1200),
}


class WorkspaceRepository:
    # @MX:ANCHOR: [AUTO] ensure_default_workspace called at startup and by many use-cases
    # @MX:REASON: Must always return a valid workspace; failure blocks entire application startup

    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_default_workspace(self) -> Workspace:
        """Return existing workspace or create a default one."""
        workspace = self.db.query(Workspace).first()
        if not workspace:
            workspace = Workspace(name="My Workspace")
            self.db.add(workspace)
            self.db.flush()
            setting = WorkspaceSetting(workspace_id=workspace.id)
            self.db.add(setting)
            self._ensure_default_feature_models(workspace.id)
            self.db.commit()
            self.db.refresh(workspace)
        else:
            changed = self._ensure_default_feature_models(workspace.id)
            if not self.get_setting(workspace.id):
                self.db.add(WorkspaceSetting(workspace_id=workspace.id))
                changed = True
            if changed:
                self.db.commit()
                self.db.refresh(workspace)
        return workspace

    def _ensure_default_feature_models(self, workspace_id: uuid.UUID) -> bool:
        changed = False
        existing = {
            m.feature_key
            for m in self.db.query(FeatureModelSetting)
            .filter_by(workspace_id=workspace_id)
            .all()
        }
        for feature_key, defaults in DEFAULT_FEATURE_MODELS.items():
            if feature_key in existing:
                continue
            provider, model, temperature, max_tokens = defaults
            self.db.add(
                FeatureModelSetting(
                    workspace_id=workspace_id,
                    feature_key=feature_key,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
            changed = True
        return changed

    def get_setting(self, workspace_id: uuid.UUID) -> WorkspaceSetting | None:
        return self.db.query(WorkspaceSetting).filter_by(workspace_id=workspace_id).first()

    def upsert_setting(self, workspace_id: uuid.UUID, updates: dict) -> WorkspaceSetting:
        setting = self.get_setting(workspace_id)
        if not setting:
            setting = WorkspaceSetting(workspace_id=workspace_id, **updates)
            self.db.add(setting)
        else:
            for k, v in updates.items():
                if hasattr(setting, k):
                    setattr(setting, k, v)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def list_feature_models(self, workspace_id: uuid.UUID) -> list[FeatureModelSetting]:
        return (
            self.db.query(FeatureModelSetting)
            .filter_by(workspace_id=workspace_id)
            .all()
        )

    def get_feature_model(
        self, workspace_id: uuid.UUID, feature_key: str
    ) -> FeatureModelSetting | None:
        return (
            self.db.query(FeatureModelSetting)
            .filter_by(workspace_id=workspace_id, feature_key=feature_key)
            .first()
        )

    def upsert_feature_model(
        self, workspace_id: uuid.UUID, feature_key: str, data: dict
    ) -> FeatureModelSetting:
        model = self.get_feature_model(workspace_id, feature_key)
        if not model:
            model = FeatureModelSetting(
                workspace_id=workspace_id, feature_key=feature_key, **data
            )
            self.db.add(model)
        else:
            for k, v in data.items():
                if hasattr(model, k):
                    setattr(model, k, v)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_trend_setting(self, workspace_id: uuid.UUID) -> WorkspaceTrendSetting | None:
        return self.db.query(WorkspaceTrendSetting).filter_by(workspace_id=workspace_id).first()

    def upsert_trend_setting(
        self, workspace_id: uuid.UUID, updates: dict
    ) -> WorkspaceTrendSetting:
        setting = self.get_trend_setting(workspace_id)
        if not setting:
            setting = WorkspaceTrendSetting(workspace_id=workspace_id, **updates)
            self.db.add(setting)
        else:
            for k, v in updates.items():
                if hasattr(setting, k):
                    setattr(setting, k, v)
        self.db.commit()
        self.db.refresh(setting)
        return setting
