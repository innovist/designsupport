"""DTOs for abstraction module request/response.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class GenerateAbstractionRulesRequest:
    """Request DTO for generating abstraction rules."""
    session_id: UUID
    concept_id: UUID
    source_refs: list[UUID]


@dataclass
class AbstractionRuleDTO:
    """DTO for abstraction rule."""
    id: UUID
    session_id: UUID
    concept_id: UUID
    axis: str
    observation: str
    applied_rule: str
    source_refs: list[UUID]
    risk_note: Optional[str]
    created_at: datetime


@dataclass
class GenerateAbstractionRulesResponse:
    """Response DTO for generated abstraction rules."""
    rules: list[AbstractionRuleDTO]
    rejected_count: int  # Number of rules rejected due to safety


@dataclass
class GenerateSketchPromptsRequest:
    """Request DTO for generating sketch prompts."""
    session_id: UUID
    concept_id: UUID


@dataclass
class SketchPromptDTO:
    """DTO for sketch prompt."""
    id: UUID
    session_id: UUID
    kind: str
    template: str
    variables: dict[str, str]
    source_refs: list[UUID]
    rendered: str
    created_at: datetime


@dataclass
class GenerateSketchPromptsResponse:
    """Response DTO for generated sketch prompts."""
    prompts: list[SketchPromptDTO]


@dataclass
class ValidatePromptSafetyRequest:
    """Request DTO for validating prompt safety."""
    session_id: UUID
    prompt_id: Optional[UUID]
    prompt_text: str
    source_refs: list[UUID]


@dataclass
class PromptSafetyViolationDTO:
    """DTO for prompt safety violation."""
    id: UUID
    session_id: UUID
    prompt_id: Optional[UUID]
    reason: str
    source_refs: list[UUID]
    created_at: datetime


@dataclass
class ValidatePromptSafetyResponse:
    """Response DTO for prompt safety validation."""
    is_safe: bool
    violations: list[PromptSafetyViolationDTO]


@dataclass
class PromptPatternDTO:
    """DTO for prompt pattern."""
    id: UUID
    name: str
    category: str
    source_reference: str
    input_slots: list[str]
    output_constraints: list[str]
    safety_rules: list[str]
    domain_tags: list[str]
    active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ListPromptPatternsRequest:
    """Request DTO for listing prompt patterns."""
    category: Optional[str] = None
    active_only: bool = True
