"""DRF serializers for Design Sessions entities.

REST Framework serializers for design sessions, briefs, and decisions.
Includes SPEC-05-API-001 required meta fields.
"""
from rest_framework import serializers

from apps.design_sessions.domain.entities import (
    PipelineStep,
    SessionMode,
    SessionStatus,
)
from shared.presentation.meta_serializer import SessionMetaMixin


class DesignSessionSerializer(SessionMetaMixin, serializers.Serializer):
    """Serializer for DesignSession entities with SPEC-05-API-001 meta fields."""

    id = serializers.UUIDField()
    project_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=[s.value for s in SessionStatus])
    version = serializers.IntegerField(min_value=1)
    started_by = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    # Meta fields from SessionMetaMixin (SPEC-05-API-001)
    current_step = serializers.IntegerField(source="current_step.value", read_only=True)
    mode = serializers.CharField(source="mode.value", read_only=True)
    evidence_refs = serializers.ListField(
        child=serializers.CharField(),
        source="evidence_refs",
        required=False,
    )
    is_hypothesis = serializers.BooleanField(required=False, default=False)
    decision_required = serializers.BooleanField(required=False, default=False)
    next_actions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    def to_representation(self, instance):
        """Convert entity to API response with meta fields.

        Args:
            instance: DesignSession entity

        Returns:
            Dictionary with all fields including meta
        """
        data = super().to_representation(instance)

        # Add computed meta fields
        data["current_step"] = self.get_current_step(instance)
        data["mode"] = self.get_mode(instance)
        data["evidence_refs"] = self.get_evidence_refs(instance)
        data["is_hypothesis"] = self.get_is_hypothesis(instance)
        data["decision_required"] = self.get_decision_required(instance)
        data["next_actions"] = self.get_next_actions(instance)

        return data


class DesignBriefSerializer(serializers.Serializer):
    """Serializer for DesignBrief entities."""

    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    purpose = serializers.CharField()
    audience = serializers.CharField()
    usage_context = serializers.CharField()
    constraints = serializers.CharField()
    result_form = serializers.CharField()
    clarifying_questions = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
    score = serializers.FloatField(min_value=0.0, max_value=1.0)


class DecisionLogSerializer(serializers.Serializer):
    """Serializer for DecisionLog entities."""

    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    step = serializers.ChoiceField(choices=[s.value for s in PipelineStep])
    action = serializers.CharField()
    actor_kind = serializers.ChoiceField(choices=["user", "auto"])
    actor_id = serializers.UUIDField()
    rationale = serializers.CharField()
    evidence_refs = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
    created_at = serializers.DateTimeField()


class SessionDetailSerializer(DesignSessionSerializer):
    """Extended session serializer with related entities."""

    brief = DesignBriefSerializer(required=False, allow_null=True)
    recent_decisions = DecisionLogSerializer(
        many=True,
        required=False,
        allow_null=True,
    )

    def to_representation(self, instance):
        """Convert to detailed representation with related entities.

        Args:
            instance: DesignSession entity

        Returns:
            Dictionary with session data and related entities
        """
        data = super().to_representation(instance)

        # Add related entities if available
        # These would be loaded from repositories in a real implementation
        data["brief"] = None
        data["recent_decisions"] = []

        return data


class SessionCreateSerializer(serializers.Serializer):
    """Serializer for creating new design sessions."""

    project_id = serializers.UUIDField()
    mode = serializers.ChoiceField(
        choices=[m.value for m in SessionMode],
        default=SessionMode.GUIDED.value,
    )
    started_by = serializers.UUIDField()


class SessionUpdateSerializer(serializers.Serializer):
    """Serializer for updating design sessions."""

    status = serializers.ChoiceField(
        choices=[s.value for s in SessionStatus],
        required=False,
    )
    current_step = serializers.ChoiceField(
        choices=[s.value for s in PipelineStep],
        required=False,
    )
