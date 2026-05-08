"""Data Transfer Objects for generation module."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from apps.generation.domain.value_objects import GenerationStatus, GenerationKind, AssetKind


@dataclass
class CreateGenerationJobRequest:
    """Request to create a generation job."""
    session_id: UUID
    kind: GenerationKind
    prompt_id: Optional[UUID] = None
    brief_id: Optional[UUID] = None
    concept_id: Optional[UUID] = None
    rule_ids: list[UUID] = None
    sketch_id: Optional[UUID] = None
    reference_ids: list[UUID] = None
    model_policy_key: str = "default"

    def __post_init__(self):
        """Initialize defaults."""
        if self.rule_ids is None:
            self.rule_ids = []
        if self.reference_ids is None:
            self.reference_ids = []


@dataclass
class GenerationJobResponse:
    """Response containing generation job details."""
    id: UUID
    session_id: UUID
    kind: GenerationKind
    prompt_id: Optional[UUID]
    brief_id: Optional[UUID]
    concept_id: Optional[UUID]
    rule_ids: list[UUID]
    sketch_id: Optional[UUID]
    reference_ids: list[UUID]
    status: GenerationStatus
    model_policy_key: str
    retries: int
    error_message: Optional[str]
    created_at: str
    updated_at: str
    completed_at: Optional[str]


@dataclass
class GeneratedDesignResponse:
    """Response containing generated design details."""
    id: UUID
    job_id: UUID
    asset_uri: str
    asset_kind: AssetKind
    parent_sketch_id: Optional[UUID]
    brief_id: Optional[UUID]
    concept_id: Optional[UUID]
    rule_ids: list[UUID]
    reference_ids: list[UUID]
    model_policy_key: str
    prompt_id: Optional[UUID]
    created_at: str


@dataclass
class ExecuteJobRequest:
    """Request to execute a generation job."""
    job_id: UUID
    force_retry: bool = False


@dataclass
class ExecuteJobResponse:
    """Response from job execution."""
    job_id: UUID
    status: GenerationStatus
    design_ids: list[UUID]
    asset_uris: list[str]
    cost_metadata: Optional[dict]
    error_message: Optional[str]
