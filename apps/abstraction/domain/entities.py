"""Domain entities for abstraction module.

This file is pure Python - no Django imports allowed.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from shared.domain.exceptions import ValidationError

from .value_objects import AbstractionAxis, SketchPromptKind, PromptCategory


@dataclass
class AbstractionRule:
    """An abstraction rule extracted from a concept.

    Represents a design principle abstracted from a concept along a specific axis.

    Attributes:
        id: Unique identifier
        session_id: Associated design session
        concept_id: Source concept candidate
        axis: Abstraction axis (form, structure, surface, color_material, meaning, usability)
        observation: What was observed in the concept
        applied_rule: The abstracted design rule
        source_refs: References to source materials (insights, analyses)
        risk_note: Optional risk note for style mimicry concerns
        created_at: Creation timestamp
    """
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(kw_only=True)
    concept_id: UUID = field(kw_only=True)
    axis: AbstractionAxis = field(kw_only=True)
    observation: str = field(kw_only=True)
    applied_rule: str = field(kw_only=True)
    source_refs: list[UUID] = field(default_factory=list, kw_only=True)
    risk_note: Optional[str] = field(default=None, kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate abstraction rule."""
        if not self.observation or not self.observation.strip():
            raise ValidationError("observation", "Observation cannot be empty")
        if not self.applied_rule or not self.applied_rule.strip():
            raise ValidationError("applied_rule", "Applied rule cannot be empty")
        if self.axis not in AbstractionAxis:
            raise ValidationError(
                "axis",
                f"Invalid axis: {self.axis}. Must be one of {[a.value for a in AbstractionAxis.all_axes()]}"
            )

    def mark_risky(self, reason: str) -> None:
        """Mark this rule as risky with a reason.

        REQ-03-ABSTRACT-005: If rule directly mimics brand/artist style → REJECT.
        """
        self.risk_note = reason


@dataclass
class SketchPrompt:
    """A prompt for generating sketches.

    Built from abstraction rules and sketch analysis data.

    Attributes:
        id: Unique identifier
        session_id: Associated design session
        kind: Type of prompt (preserve_original or expand_concept)
        template: Prompt template with variable placeholders
        variables: Variable values for template substitution
        source_refs: References to abstraction rules used
        created_at: Creation timestamp
    """
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(kw_only=True)
    kind: SketchPromptKind = field(kw_only=True)
    template: str = field(kw_only=True)
    variables: dict[str, str] = field(default_factory=dict, kw_only=True)
    source_refs: list[UUID] = field(default_factory=list, kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate sketch prompt."""
        if not self.template or not self.template.strip():
            raise ValidationError("template", "Template cannot be empty")
        if self.kind not in SketchPromptKind:
            raise ValidationError(
                "kind",
                f"Invalid kind: {self.kind}. Must be one of {[k.value for k in SketchPromptKind]}"
            )

    def render(self) -> str:
        """Render the prompt by substituting variables into template."""
        rendered = self.template
        for key, value in self.variables.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, value)
        return rendered


@dataclass
class PromptPattern:
    """A reusable prompt pattern in the library.

    REQ-03-PROMPT-001: Prompt pattern library with safety validation.

    Attributes:
        id: Unique identifier
        name: Pattern name
        category: Pattern category
        source_reference: Reference to source material or documentation
        input_slots: Required input variables for the pattern
        output_constraints: Constraints on the output
        safety_rules: Safety rules to validate
        domain_tags: Domain-specific tags for categorization
        active: Whether this pattern is active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    id: UUID = field(default_factory=uuid4)
    name: str = field(kw_only=True)
    category: PromptCategory = field(kw_only=True)
    source_reference: str = field(kw_only=True)
    input_slots: list[str] = field(default_factory=list, kw_only=True)
    output_constraints: list[str] = field(default_factory=list, kw_only=True)
    safety_rules: list[str] = field(default_factory=list, kw_only=True)
    domain_tags: list[str] = field(default_factory=list, kw_only=True)
    active: bool = field(default=True, kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate prompt pattern."""
        if not self.name or not self.name.strip():
            raise ValidationError("name", "Name cannot be empty")
        if not self.source_reference or not self.source_reference.strip():
            raise ValidationError("source_reference", "Source reference cannot be empty")
        if self.category not in PromptCategory:
            raise ValidationError(
                "category",
                f"Invalid category: {self.category}"
            )

    def deactivate(self) -> None:
        """Deactivate this pattern."""
        self.active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """Activate this pattern."""
        self.active = True
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class PromptSafetyViolation:
    """A recorded safety violation for a prompt.

    REQ-03-PROMPT-006: Record safety violations for auditing.

    Attributes:
        id: Unique identifier
        session_id: Associated design session
        prompt_id: Optional ID of the violating prompt
        reason: Reason for the violation
        source_refs: References to violated rules
        created_at: Creation timestamp
    """
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(kw_only=True)
    prompt_id: Optional[UUID] = field(default=None, kw_only=True)
    reason: str = field(kw_only=True)
    source_refs: list[UUID] = field(default_factory=list, kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate safety violation."""
        if not self.reason or not self.reason.strip():
            raise ValidationError("reason", "Reason cannot be empty")
