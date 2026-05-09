"""
DTOs for sketch upload and analysis.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SketchAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sketch_id: uuid.UUID
    intent: Optional[str]
    intent_is_hypothesis: bool
    form_elements: Optional[list]
    structure_elements: Optional[list]
    unclear_points: Optional[list]
    questions_for_user: Optional[list]
    keep_elements: Optional[list]
    vary_elements: Optional[list]
    user_confirmed: bool
    user_corrections: Optional[dict]


class SketchAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    file_path: str
    image_url: str
    description: Optional[str]
    original_filename: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    user_memo: Optional[str]
    created_at: datetime
    analysis: Optional[SketchAnalysisResponse] = None


class SketchConfirmRequest(BaseModel):
    confirmed: bool
    corrections: Optional[dict] = None
