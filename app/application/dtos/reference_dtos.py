"""
DTOs for reference assets and analysis.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReferenceAnalysisSummary(BaseModel):
    """Embedded analysis summary for reference cards."""
    model_config = ConfigDict(from_attributes=True)

    form_grammar: Optional[str] = None
    structure_grammar: Optional[str] = None
    material_direction: Optional[str] = None
    replication_risk: Optional[str] = None
    abstraction_fitness: Optional[float] = None


class ReferenceAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    asset_type: str
    url: Optional[str]
    source_url: Optional[str]
    title: Optional[str]
    thumbnail_path: Optional[str]
    thumbnail_url: Optional[str]
    source_domain: Optional[str]
    license_type: Optional[str]
    copyright_risk: str
    high_risk_blocked: bool
    collected_at: datetime
    published_at: Optional[datetime]
    domain_tags: Optional[list]
    relevance_reason: Optional[str]
    abstraction_elements: Optional[dict]
    analysis: Optional[ReferenceAnalysisSummary] = None


class ReferenceAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference_id: uuid.UUID
    form_grammar: Optional[str]
    structure_grammar: Optional[str]
    material_direction: Optional[str]
    meaning_symbols: Optional[str]
    usability_notes: Optional[str]
    replication_risk: Optional[str]
    abstraction_fitness: Optional[float]


class ReferenceRiskUpdate(BaseModel):
    copyright_risk: str  # low | medium | high | unknown
    license_type: Optional[str] = None
