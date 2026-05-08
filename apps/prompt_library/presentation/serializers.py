"""DRF serializers for prompt library API."""
from rest_framework import serializers

from apps.prompt_library.domain import PromptPattern, PromptSafetyViolation
from apps.abstraction.domain.value_objects import PromptCategory


class PromptPatternSerializer(serializers.Serializer):
    """Serializer for PromptPattern entity."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    category = serializers.ChoiceField(choices=[c.value for c in PromptCategory])
    source_reference = serializers.CharField()
    input_slots = serializers.ListField(child=serializers.CharField(), default=list)
    output_constraints = serializers.ListField(child=serializers.CharField(), default=list)
    safety_rules = serializers.ListField(child=serializers.CharField(), default=list)
    domain_tags = serializers.ListField(child=serializers.CharField(), default=list)
    active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        """Convert domain entity to API representation."""
        return {
            'id': str(instance.id),
            'name': instance.name,
            'category': instance.category.value,
            'source_reference': instance.source_reference,
            'input_slots': instance.input_slots,
            'output_constraints': instance.output_constraints,
            'safety_rules': instance.safety_rules,
            'domain_tags': instance.domain_tags,
            'active': instance.active,
            'created_at': instance.created_at.isoformat(),
            'updated_at': instance.updated_at.isoformat(),
        }

    def to_internal_value(self, data):
        """Convert API data to domain entity fields."""
        return {
            'name': data.get('name'),
            'category': PromptCategory(data.get('category')),
            'source_reference': data.get('source_reference'),
            'input_slots': data.get('input_slots', []),
            'output_constraints': data.get('output_constraints', []),
            'safety_rules': data.get('safety_rules', []),
            'domain_tags': data.get('domain_tags', []),
            'active': data.get('active', True),
        }


class PromptSafetyViolationSerializer(serializers.Serializer):
    """Serializer for PromptSafetyViolation entity."""

    id = serializers.UUIDField(read_only=True)
    session_id = serializers.UUIDField()
    prompt_id = serializers.UUIDField(allow_null=True, required=False)
    reason = serializers.CharField()
    source_refs = serializers.ListField(child=serializers.UUIDField(), default=list)
    created_at = serializers.DateTimeField(read_only=True)

    def to_representation(self, instance):
        """Convert domain entity to API representation."""
        return {
            'id': str(instance.id),
            'session_id': str(instance.session_id),
            'prompt_id': str(instance.prompt_id) if instance.prompt_id else None,
            'reason': instance.reason,
            'source_refs': [str(ref) for ref in instance.source_refs],
            'created_at': instance.created_at.isoformat(),
        }

    def to_internal_value(self, data):
        """Convert API data to domain entity fields."""
        from uuid import UUID

        source_refs = data.get('source_refs', [])
        return {
            'session_id': UUID(data.get('session_id')),
            'prompt_id': UUID(data.get('prompt_id')) if data.get('prompt_id') else None,
            'reason': data.get('reason'),
            'source_refs': [UUID(ref) for ref in source_refs],
        }


class SearchPatternsRequestSerializer(serializers.Serializer):
    """Serializer for search patterns request."""

    category = serializers.ChoiceField(
        choices=[c.value for c in PromptCategory],
        required=False,
        allow_null=True,
    )
    domain_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
    )


class ValidatePromptRequestSerializer(serializers.Serializer):
    """Serializer for validate prompt request."""

    session_id = serializers.UUIDField()
    prompt_id = serializers.UUIDField(allow_null=True, required=False)
    prompt_text = serializers.CharField(min_length=1)


class ValidatePromptResponseSerializer(serializers.Serializer):
    """Serializer for validate prompt response."""

    is_safe = serializers.BooleanField()
    violations = PromptSafetyViolationSerializer(many=True)
