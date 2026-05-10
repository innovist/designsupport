"""
DTOs for image generation and evaluation.
"""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class GenerationRequest(BaseModel):
    rule_id: Optional[uuid.UUID] = None
    brief_id: Optional[uuid.UUID] = None
    concept_id: Optional[uuid.UUID] = None
    is_from_user_sketch: bool = False
    output_kind: Literal["draft", "final"] = "draft"
    source_draft_id: Optional[uuid.UUID] = None  # 최종안 생성 시 기반 초안 ID
    feedback_note: Optional[str] = None  # 최종안 생성 시 사용자 피드백


class GeneratedDesignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    rule_id: Optional[uuid.UUID]
    concept_id: Optional[uuid.UUID]
    prompt: str
    provider: Optional[str]
    model: Optional[str]
    image_path: Optional[str]
    image_url: Optional[str]
    status: str
    failure_reason: Optional[str]
    generation_params: Optional[dict]
    is_from_user_sketch: bool
    created_at: datetime


class SpecDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    version: int
    content_json: dict
    status: str
    parent_version_id: Optional[uuid.UUID]
    selected_design_id: Optional[uuid.UUID] = None


class SpecGenerationRequest(BaseModel):
    selected_design_id: Optional[uuid.UUID] = None
