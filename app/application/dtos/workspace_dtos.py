"""
Request / response DTOs for the workspace domain.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WorkspaceSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    default_domain: Optional[str]
    recency_days: int
    spec_sections_config: Optional[dict]


class WorkspaceSettingUpdate(BaseModel):
    default_domain: Optional[str] = None
    recency_days: Optional[int] = None
    spec_sections_config: Optional[dict] = None


class FeatureModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    feature_key: str
    provider: str
    model: str
    temperature: float
    max_tokens: int
    retry_count: int
    fallback_provider: Optional[str]
    fallback_model: Optional[str]
    fallback_retry_count: int
    extra_params: Optional[dict]


class FeatureModelUpdate(BaseModel):
    provider: str
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    retry_count: Optional[int] = 2
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    fallback_retry_count: Optional[int] = 1
    extra_params: Optional[dict] = None


class TrendSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    enabled_source_ids: Optional[list]
    default_domain: Optional[str]
    recency_days: int


class TrendSettingUpdate(BaseModel):
    enabled_source_ids: Optional[list] = None
    default_domain: Optional[str] = None
    recency_days: Optional[int] = None
