"""
Workspace-level ORM models: settings, per-feature AI model configuration,
and trend source preferences.
"""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspace"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="My Workspace")

    # relationships
    setting: Mapped["WorkspaceSetting"] = relationship(
        "WorkspaceSetting", back_populates="workspace", uselist=False
    )
    feature_models: Mapped[list["FeatureModelSetting"]] = relationship(
        "FeatureModelSetting", back_populates="workspace"
    )
    trend_setting: Mapped["WorkspaceTrendSetting"] = relationship(
        "WorkspaceTrendSetting", back_populates="workspace", uselist=False
    )
    projects: Mapped[list["DesignProject"]] = relationship(  # type: ignore[name-defined]
        "DesignProject", back_populates="workspace"
    )


class WorkspaceSetting(Base, TimestampMixin):
    __tablename__ = "workspace_setting"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    default_domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recency_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    spec_sections_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="setting")


class FeatureModelSetting(Base, TimestampMixin):
    """
    Stores which AI provider/model to use for each pipeline feature.

    feature_key values:
      brief_structuring, trend_analysis, concept_generation, reference_analysis,
      sketch_analysis, abstraction, sketch_prompt_generation, sketch_generation,
      final_image_prompt_generation, final_image_generation, spec_writing, chat
    """

    # @MX:ANCHOR: [AUTO] Central routing table for all AI model selection
    # @MX:REASON: AI client factory reads this table; wrong data causes all AI calls to fail

    __tablename__ = "feature_model_setting"
    __table_args__ = (
        UniqueConstraint("workspace_id", "feature_key", name="uq_feature_model_workspace_feature"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    feature_key: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    fallback_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fallback_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fallback_retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    extra_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="feature_models")


class WorkspaceTrendSetting(Base, TimestampMixin):
    __tablename__ = "workspace_trend_setting"
    __table_args__ = (
        UniqueConstraint("workspace_id", name="uq_trend_setting_workspace"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspace.id", ondelete="CASCADE"), nullable=False
    )
    enabled_source_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    default_domain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recency_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="trend_setting")
