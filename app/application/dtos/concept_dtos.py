"""
DTOs for concept candidates and decisions.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConceptCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    name: str
    description: Optional[str]
    score: Optional[float]
    rationale: Optional[str]
    risk: Optional[str]
    evidence_ids: Optional[list]
    trend_evidence: Optional[list]
    status: str
    generated_by: str


class ConceptDecisionCreate(BaseModel):
    decision: str  # adopt | hold | discard | explore
    reason: Optional[str] = None


class ConceptDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    decision: str
    decider: str
    reason: Optional[str]
