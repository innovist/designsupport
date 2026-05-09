"""
DTOs for image generation and evaluation.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class GenerationRequest(BaseModel):
    rule_id: uuid.UUID
    brief_id: Optional[uuid.UUID] = None
    concept_id: Optional[uuid.UUID] = None
    is_from_user_sketch: bool = False


class GeneratedDesignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    rule_id: uuid.UUID
    prompt: str
    provider: Optional[str]
    model: Optional[str]
    image_path: Optional[str]
    image_url: Optional[str]
    status: str
    failure_reason: Optional[str]
    is_from_user_sketch: bool


class SpecDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    version: int
    content_json: dict
    status: str
    parent_version_id: Optional[uuid.UUID]
