"""Django REST serializers for abstraction module."""
from rest_framework import serializers

from apps.abstraction.application.dtos import (
    AbstractionRuleDTO,
    SketchPromptDTO,
    PromptSafetyViolationDTO,
    PromptPatternDTO,
    GenerateAbstractionRulesRequest,
    GenerateSketchPromptsRequest,
    ValidatePromptSafetyRequest,
    ListPromptPatternsRequest,
)


class GenerateAbstractionRulesSerializer(serializers.Serializer):
    """Serializer for generating abstraction rules."""

    session_id = serializers.UUIDField()
    concept_id = serializers.UUIDField()
    source_refs = serializers.ListField(child=serializers.UUIDField())

    def to_request_dto(self) -> GenerateAbstractionRulesRequest:
        """Convert to request DTO."""
        return GenerateAbstractionRulesRequest(
            session_id=self.validated_data["session_id"],
            concept_id=self.validated_data["concept_id"],
            source_refs=self.validated_data["source_refs"],
        )


class AbstractionRuleSerializer(serializers.Serializer):
    """Serializer for abstraction rule DTO."""

    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    concept_id = serializers.UUIDField()
    axis = serializers.ChoiceField(
        choices=[
            "form",
            "structure",
            "surface",
            "color_material",
            "meaning",
            "usability",
        ]
    )
    observation = serializers.CharField()
    applied_rule = serializers.CharField()
    source_refs = serializers.ListField(child=serializers.UUIDField())
    risk_note = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: AbstractionRuleDTO) -> 'AbstractionRuleSerializer':
        """Create serializer from DTO."""
        return cls(data={
            "id": dto.id,
            "session_id": dto.session_id,
            "concept_id": dto.concept_id,
            "axis": dto.axis,
            "observation": dto.observation,
            "applied_rule": dto.applied_rule,
            "source_refs": dto.source_refs,
            "risk_note": dto.risk_note,
            "created_at": dto.created_at,
        })


class GenerateSketchPromptsSerializer(serializers.Serializer):
    """Serializer for generating sketch prompts."""

    session_id = serializers.UUIDField()
    concept_id = serializers.UUIDField()

    def to_request_dto(self) -> GenerateSketchPromptsRequest:
        """Convert to request DTO."""
        return GenerateSketchPromptsRequest(
            session_id=self.validated_data["session_id"],
            concept_id=self.validated_data["concept_id"],
        )


class SketchPromptSerializer(serializers.Serializer):
    """Serializer for sketch prompt DTO."""

    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    kind = serializers.ChoiceField(
        choices=["preserve_original", "expand_concept"]
    )
    template = serializers.CharField()
    variables = serializers.DictField(child=serializers.CharField())
    source_refs = serializers.ListField(child=serializers.UUIDField())
    rendered = serializers.CharField()
    created_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: SketchPromptDTO) -> 'SketchPromptSerializer':
        """Create serializer from DTO."""
        return cls(data={
            "id": dto.id,
            "session_id": dto.session_id,
            "kind": dto.kind,
            "template": dto.template,
            "variables": dto.variables,
            "source_refs": dto.source_refs,
            "rendered": dto.rendered,
            "created_at": dto.created_at,
        })


class ValidatePromptSafetySerializer(serializers.Serializer):
    """Serializer for validating prompt safety."""

    session_id = serializers.UUIDField()
    prompt_id = serializers.UUIDField(allow_null=True, required=False)
    prompt_text = serializers.CharField()
    source_refs = serializers.ListField(child=serializers.UUIDField())

    def to_request_dto(self) -> ValidatePromptSafetyRequest:
        """Convert to request DTO."""
        return ValidatePromptSafetyRequest(
            session_id=self.validated_data["session_id"],
            prompt_id=self.validated_data.get("prompt_id"),
            prompt_text=self.validated_data["prompt_text"],
            source_refs=self.validated_data["source_refs"],
        )


class PromptSafetyViolationSerializer(serializers.Serializer):
    """Serializer for prompt safety violation DTO."""

    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    prompt_id = serializers.UUIDField(allow_null=True, required=False)
    reason = serializers.CharField()
    source_refs = serializers.ListField(child=serializers.UUIDField())
    created_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: PromptSafetyViolationDTO) -> 'PromptSafetyViolationSerializer':
        """Create serializer from DTO."""
        return cls(data={
            "id": dto.id,
            "session_id": dto.session_id,
            "prompt_id": dto.prompt_id,
            "reason": dto.reason,
            "source_refs": dto.source_refs,
            "created_at": dto.created_at,
        })


class PromptPatternSerializer(serializers.Serializer):
    """Serializer for prompt pattern DTO."""

    id = serializers.UUIDField()
    name = serializers.CharField()
    category = serializers.ChoiceField(
        choices=[
            "line_to_render",
            "multi_reference_fusion",
            "product_packaging",
            "material_texture",
            "exploded_view",
            "storyboard",
            "moodboard_collage",
            "diagram_annotation",
            "domain_application",
            "refinement_preserve_original",
        ]
    )
    source_reference = serializers.CharField()
    input_slots = serializers.ListField(child=serializers.CharField())
    output_constraints = serializers.ListField(child=serializers.CharField())
    safety_rules = serializers.ListField(child=serializers.CharField())
    domain_tags = serializers.ListField(child=serializers.CharField())
    active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: PromptPatternDTO) -> 'PromptPatternSerializer':
        """Create serializer from DTO."""
        return cls(data={
            "id": dto.id,
            "name": dto.name,
            "category": dto.category,
            "source_reference": dto.source_reference,
            "input_slots": dto.input_slots,
            "output_constraints": dto.output_constraints,
            "safety_rules": dto.safety_rules,
            "domain_tags": dto.domain_tags,
            "active": dto.active,
            "created_at": dto.created_at,
            "updated_at": dto.updated_at,
        })


class ListPromptPatternsSerializer(serializers.Serializer):
    """Serializer for listing prompt patterns."""

    category = serializers.CharField(allow_null=True, required=False)
    active_only = serializers.BooleanField(default=True)

    def to_request_dto(self) -> ListPromptPatternsRequest:
        """Convert to request DTO."""
        return ListPromptPatternsRequest(
            category=self.validated_data.get("category"),
            active_only=self.validated_data.get("active_only", True),
        )
