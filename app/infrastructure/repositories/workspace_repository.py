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

# @MX:NOTE: [AUTO] Default AI model configuration per feature — mapped to catalog-valid models.
# Mapping rationale:
#   - brief_structuring / chat: fast response → deepseek-v4-flash
#   - trend_analysis / abstraction / spec_writing: deep analysis → deepseek-v4-pro
#   - concept_generation: creative generation → qwen3.6-max-preview
#   - reference_analysis / sketch_analysis: multimodal → gemini-3-flash-preview / gpt-5.4-mini
#   - sketch/image generation: image model → gemini-2.5-flash-image
DEFAULT_FEATURE_MODELS = {
    "brief_structuring":            ("deepseek", "deepseek-v4-flash",       0.3, 1000),
    "trend_analysis":               ("deepseek", "deepseek-v4-pro",         0.3, 1200),
    "concept_generation":           ("alibaba",  "qwen3.6-max-preview",     0.7, 2000),
    "reference_analysis":           ("gemini",   "gemini-3-flash-preview",  0.3, 1200),
    "sketch_analysis":              ("openai",   "gpt-5.4-mini",            0.3, 1200),
    "abstraction":                  ("deepseek", "deepseek-v4-pro",         0.4, 2000),
    "sketch_prompt_generation":     ("openai",   "gpt-5.4-mini",            0.35, 1000),
    "sketch_generation":            ("gemini",   "gemini-2.5-flash-image",  0.7, 2000),
    "final_image_prompt_generation":("openai",   "gpt-5.4-mini",            0.35, 1000),
    "final_image_generation":       ("gemini",   "gemini-2.5-flash-image",  0.7, 2000),
    "spec_writing":                 ("deepseek", "deepseek-v4-pro",         0.3, 3000),
    "chat":                         ("deepseek", "deepseek-v4-flash",       0.7, 2000),
    "image_generation":             ("gemini",   "gemini-2.5-flash-image",  0.7, 2000),
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
        """Insert defaults for any missing feature keys. Never overwrites user-configured settings."""
        changed = False
        existing_keys: set[str] = {
            m.feature_key
            for m in self.db.query(FeatureModelSetting)
            .filter_by(workspace_id=workspace_id)
            .all()
        }
        for feature_key, defaults in DEFAULT_FEATURE_MODELS.items():
            if feature_key not in existing_keys:
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
