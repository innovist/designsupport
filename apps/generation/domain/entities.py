"""Domain entities for generation module.

This file is pure Python - no Django imports allowed.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from shared.domain.exceptions import ValidationError
from apps.generation.domain.value_objects import (
    GenerationStatus,
    GenerationKind,
    AssetKind
)


@dataclass
class CostMetadata:
    """Cost tracking for generation operations.

    Attributes:
        model_key: Model identifier (e.g., "seedream-4.5")
        prompt_tokens: Input tokens used
        completion_tokens: Output tokens used
        total_tokens: Total tokens
        cost_usd: Estimated cost in USD
    """
    model_key: str = field(kw_only=True)
    prompt_tokens: int = field(default=0, kw_only=True)
    completion_tokens: int = field(default=0, kw_only=True)
    total_tokens: int = field(default=0, kw_only=True)
    cost_usd: float = field(default=0.0, kw_only=True)

    def __post_init__(self):
        """Validate cost metadata."""
        if self.prompt_tokens < 0:
            raise ValidationError("prompt_tokens", "Cannot be negative")
        if self.completion_tokens < 0:
            raise ValidationError("completion_tokens", "Cannot be negative")
        if self.total_tokens < 0:
            raise ValidationError("total_tokens", "Cannot be negative")
        if self.cost_usd < 0:
            raise ValidationError("cost_usd", "Cannot be negative")


@dataclass
class GenerationJob:
    """A generation job for creating design assets.

    Attributes:
        id: Unique identifier
        session_id: Associated design session
        kind: Type of generation (sketch/refinement/variation/domain_application)
        prompt_id: Associated prompt (optional for some kinds)
        brief_id: Associated design brief (optional)
        concept_id: Associated concept (optional)
        rule_ids: Abstraction rules to apply (for variations)
        sketch_id: Parent UserSketchAsset for refinements (optional)
        reference_ids: Reference materials (optional)
        status: Current job status
        model_policy_key: Model routing policy key
        retries: Number of retry attempts
        cost_meta: Cost tracking metadata
        error_message: Error details if failed
        created_at: Creation timestamp
        updated_at: Last update timestamp
        completed_at: Completion timestamp (when terminal)
    """
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(kw_only=True)
    kind: GenerationKind = field(kw_only=True)
    prompt_id: Optional[UUID] = field(default=None, kw_only=True)
    brief_id: Optional[UUID] = field(default=None, kw_only=True)
    concept_id: Optional[UUID] = field(default=None, kw_only=True)
    rule_ids: list[UUID] = field(default_factory=list, kw_only=True)
    sketch_id: Optional[UUID] = field(default=None, kw_only=True)
    reference_ids: list[UUID] = field(default_factory=list, kw_only=True)
    status: GenerationStatus = field(default=GenerationStatus.QUEUED, kw_only=True)
    model_policy_key: str = field(kw_only=True)
    retries: int = field(default=0, kw_only=True)
    cost_meta: Optional[CostMetadata] = field(default=None, kw_only=True)
    error_message: Optional[str] = field(default=None, kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = field(default=None, kw_only=True)

    def __post_init__(self):
        """Validate generation job."""
        if not self.model_policy_key or not self.model_policy_key.strip():
            raise ValidationError("model_policy_key", "Model policy key cannot be empty")

        # REQ-03-GEN-002: Must link to at least one of: brief, concept, rule, reference
        has_brief = self.brief_id is not None
        has_concept = self.concept_id is not None
        has_rules = len(self.rule_ids) > 0
        has_references = len(self.reference_ids) > 0

        if not (has_brief or has_concept or has_rules or has_references):
            raise ValidationError(
                "links",
                "Job must link to at least one of: brief, concept, rule, or reference"
            )

        # Kind-specific validation
        if self.kind == GenerationKind.REFINEMENT:
            if self.sketch_id is None:
                raise ValidationError(
                    "sketch_id",
                    "Refinement jobs require a parent sketch"
                )
        if self.kind == GenerationKind.VARIATION:
            if len(self.rule_ids) == 0:
                raise ValidationError(
                    "rule_ids",
                    "Variation jobs require at least one abstraction rule"
                )

        if self.retries < 0:
            raise ValidationError("retries", "Retries cannot be negative")

    def transition_to(self, new_status: GenerationStatus, error: Optional[str] = None) -> None:
        """Transition to a new status if valid."""
        if not self.status.can_transition_to(new_status):
            raise ValidationError(
                "status",
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )

        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

        if new_status.is_terminal():
            self.completed_at = datetime.now(timezone.utc)

        if error and new_status == GenerationStatus.FAILED:
            self.error_message = error

    def increment_retry(self) -> None:
        """Increment retry counter and reset to queued."""
        self.retries += 1
        self.status = GenerationStatus.QUEUED
        self.updated_at = datetime.now(timezone.utc)
        self.error_message = None

    def update_cost(self, cost_meta: CostMetadata) -> None:
        """Update cost metadata."""
        self.cost_meta = cost_meta
        self.updated_at = datetime.now(timezone.utc)

    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if job can be retried."""
        return self.status == GenerationStatus.FAILED and self.retries < max_retries


@dataclass
class GeneratedDesign:
    """A generated design asset.

    Attributes:
        id: Unique identifier
        job_id: Associated generation job
        asset_uri: URI to the generated asset (in object storage)
        asset_kind: Type of asset
        parent_sketch_id: Original UserSketchAsset for refinements (optional)
        brief_id: Associated design brief
        concept_id: Associated concept
        rule_ids: Abstraction rules applied (for variations)
        reference_ids: References used in generation
        model_policy_key: Model used for generation
        prompt_id: Prompt used for generation
        created_at: Creation timestamp
    """
    id: UUID = field(default_factory=uuid4)
    job_id: UUID = field(kw_only=True)
    asset_uri: str = field(kw_only=True)
    asset_kind: AssetKind = field(kw_only=True)
    parent_sketch_id: Optional[UUID] = field(default=None, kw_only=True)
    brief_id: Optional[UUID] = field(default=None, kw_only=True)
    concept_id: Optional[UUID] = field(default=None, kw_only=True)
    rule_ids: list[UUID] = field(default_factory=list, kw_only=True)
    reference_ids: list[UUID] = field(default_factory=list, kw_only=True)
    model_policy_key: str = field(kw_only=True)
    prompt_id: Optional[UUID] = field(default=None, kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate generated design."""
        if not self.asset_uri or not self.asset_uri.strip():
            raise ValidationError("asset_uri", "Asset URI cannot be empty")
        if not self.model_policy_key or not self.model_policy_key.strip():
            raise ValidationError("model_policy_key", "Model policy key cannot be empty")
