"""
Request / response DTOs for projects, sessions, briefs, and chat.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- Project ----------

class ProjectCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    purpose: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    domain: Optional[str]
    purpose: Optional[str]
    status: str
    created_at: datetime


# ---------- Session ----------

class SessionCreate(BaseModel):
    project_id: uuid.UUID
    mode: str = "chatbot"  # chatbot | auto | sketch


class BriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    purpose: str
    domain: Optional[str]
    target_user: Optional[str]
    context: Optional[str]
    constraints: Optional[str]
    use_case: Optional[str]
    result_form: Optional[str]
    is_complete: bool


class BriefUpdate(BaseModel):
    purpose: Optional[str] = None
    domain: Optional[str] = None
    target_user: Optional[str] = None
    context: Optional[str] = None
    constraints: Optional[str] = None
    use_case: Optional[str] = None
    result_form: Optional[str] = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    mode: str
    pipeline_stage: str
    status: str
    created_at: datetime
    brief: Optional[BriefResponse] = None


class SessionStageUpdate(BaseModel):
    pipeline_stage: str


# ---------- Chat ----------

class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    stage: Optional[str]
    evidence_links: Optional[list]
    created_at: datetime
