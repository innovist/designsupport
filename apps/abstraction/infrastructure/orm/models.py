"""Django ORM models for abstraction module."""
from django.db import models

from shared.infrastructure.orm.base_model import TimestampedModel


class AbstractionRuleModel(TimestampedModel):
    """Django model for AbstractionRule entity."""

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    concept_id = models.UUIDField(db_index=True)
    axis = models.CharField(
        max_length=20,
        choices=[
            ("form", "Form"),
            ("structure", "Structure"),
            ("surface", "Surface"),
            ("color_material", "Color Material"),
            ("meaning", "Meaning"),
            ("usability", "Usability"),
        ],
    )
    observation = models.TextField()
    applied_rule = models.TextField()
    source_refs = models.JSONField(default=list)  # List of UUIDs
    risk_note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "abstraction_rules"
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["concept_id"]),
            models.Index(fields=["axis"]),
            models.Index(fields=["created_at"]),
        ]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.abstraction.domain.entities import AbstractionRule
        from apps.abstraction.domain.value_objects import AbstractionAxis
        from uuid import UUID

        return AbstractionRule(
            id=UUID(str(self.id)),
            session_id=UUID(str(self.session_id)),
            concept_id=UUID(str(self.concept_id)),
            axis=AbstractionAxis(self.axis),
            observation=self.observation,
            applied_rule=self.applied_rule,
            source_refs=[UUID(str(ref)) for ref in self.source_refs],
            risk_note=self.risk_note,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, rule):
        """Create ORM model from domain entity."""
        return cls(
            id=str(rule.id),
            session_id=str(rule.session_id),
            concept_id=str(rule.concept_id),
            axis=rule.axis.value,
            observation=rule.observation,
            applied_rule=rule.applied_rule,
            source_refs=[str(ref) for ref in rule.source_refs],
            risk_note=rule.risk_note,
            created_at=rule.created_at,
        )


class SketchPromptModel(TimestampedModel):
    """Django model for SketchPrompt entity."""

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    kind = models.CharField(
        max_length=30,
        choices=[
            ("preserve_original", "Preserve Original"),
            ("expand_concept", "Expand Concept"),
        ],
    )
    template = models.TextField()
    variables = models.JSONField(default=dict)  # Dict[str, str]
    source_refs = models.JSONField(default=list)  # List of UUIDs

    class Meta:
        db_table = "sketch_prompts"
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["kind"]),
            models.Index(fields=["created_at"]),
        ]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.abstraction.domain.entities import SketchPrompt
        from apps.abstraction.domain.value_objects import SketchPromptKind
        from uuid import UUID

        return SketchPrompt(
            id=UUID(str(self.id)),
            session_id=UUID(str(self.session_id)),
            kind=SketchPromptKind(self.kind),
            template=self.template,
            variables=self.variables,
            source_refs=[UUID(str(ref)) for ref in self.source_refs],
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, prompt):
        """Create ORM model from domain entity."""
        return cls(
            id=str(prompt.id),
            session_id=str(prompt.session_id),
            kind=prompt.kind.value,
            template=prompt.template,
            variables=prompt.variables,
            source_refs=[str(ref) for ref in prompt.source_refs],
            created_at=prompt.created_at,
        )


class PromptPatternModel(TimestampedModel):
    """Django model for PromptPattern entity."""

    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ("line_to_render", "Line to Render"),
            ("multi_reference_fusion", "Multi Reference Fusion"),
            ("product_packaging", "Product Packaging"),
            ("material_texture", "Material Texture"),
            ("exploded_view", "Exploded View"),
            ("storyboard", "Storyboard"),
            ("moodboard_collage", "Moodboard Collage"),
            ("diagram_annotation", "Diagram Annotation"),
            ("domain_application", "Domain Application"),
            ("refinement_preserve_original", "Refinement Preserve Original"),
        ],
    )
    source_reference = models.TextField()
    input_slots = models.JSONField(default=list)  # List[str]
    output_constraints = models.JSONField(default=list)  # List[str]
    safety_rules = models.JSONField(default=list)  # List[str]
    domain_tags = models.JSONField(default=list)  # List[str]
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "prompt_patterns"
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["active"]),
            models.Index(fields=["created_at"]),
        ]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.abstraction.domain.entities import PromptPattern
        from apps.abstraction.domain.value_objects import PromptCategory
        from uuid import UUID

        return PromptPattern(
            id=UUID(str(self.id)),
            name=self.name,
            category=PromptCategory(self.category),
            source_reference=self.source_reference,
            input_slots=self.input_slots,
            output_constraints=self.output_constraints,
            safety_rules=self.safety_rules,
            domain_tags=self.domain_tags,
            active=self.active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, pattern):
        """Create ORM model from domain entity."""
        return cls(
            id=str(pattern.id),
            name=pattern.name,
            category=pattern.category.value,
            source_reference=pattern.source_reference,
            input_slots=pattern.input_slots,
            output_constraints=pattern.output_constraints,
            safety_rules=pattern.safety_rules,
            domain_tags=pattern.domain_tags,
            active=pattern.active,
            created_at=pattern.created_at,
            updated_at=pattern.updated_at,
        )


class PromptSafetyViolationModel(TimestampedModel):
    """Django model for PromptSafetyViolation entity."""

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    prompt_id = models.UUIDField(null=True, blank=True, db_index=True)
    reason = models.TextField()
    source_refs = models.JSONField(default=list)  # List of UUIDs

    class Meta:
        db_table = "prompt_safety_violations"
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["prompt_id"]),
            models.Index(fields=["created_at"]),
        ]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.abstraction.domain.entities import PromptSafetyViolation
        from uuid import UUID

        return PromptSafetyViolation(
            id=UUID(str(self.id)),
            session_id=UUID(str(self.session_id)),
            prompt_id=UUID(str(self.prompt_id)) if self.prompt_id else None,
            reason=self.reason,
            source_refs=[UUID(str(ref)) for ref in self.source_refs],
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, violation):
        """Create ORM model from domain entity."""
        return cls(
            id=str(violation.id),
            session_id=str(violation.session_id),
            prompt_id=str(violation.prompt_id) if violation.prompt_id else None,
            reason=violation.reason,
            source_refs=[str(ref) for ref in violation.source_refs],
            created_at=violation.created_at,
        )
