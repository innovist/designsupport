"""Django REST serializers for concepts module."""
from rest_framework import serializers

from apps.concepts.application.dtos import (
    ConceptCandidateDTO,
    ConceptDecisionDTO,
    DecideConceptRequest,
    ProposeConceptRequest,
)


class ProposeConceptSerializer(serializers.Serializer):
    """Serializer for proposing a concept."""

    session_id = serializers.UUIDField()
    title = serializers.CharField(max_length=500)
    description = serializers.CharField()
    rationale = serializers.CharField()
    rationale_refs = serializers.ListField(child=serializers.UUIDField())
    domain_tags = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    created_by = serializers.UUIDField()

    def to_request_dto(self) -> ProposeConceptRequest:
        """Convert to request DTO."""
        return ProposeConceptRequest(
            session_id=self.validated_data["session_id"],
            title=self.validated_data["title"],
            description=self.validated_data["description"],
            rationale=self.validated_data["rationale"],
            rationale_refs=self.validated_data["rationale_refs"],
            domain_tags=self.validated_data.get("domain_tags", []),
            created_by=self.validated_data["created_by"],
        )


class DecideConceptSerializer(serializers.Serializer):
    """Serializer for deciding on a concept."""

    concept_id = serializers.UUIDField()
    decision = serializers.ChoiceField(
        choices=["adopt", "hold", "discard", "explore_more"]
    )
    actor_kind = serializers.ChoiceField(choices=["user", "auto"])
    actor_id = serializers.UUIDField()
    rationale = serializers.CharField()

    def to_request_dto(self) -> DecideConceptRequest:
        """Convert to request DTO."""
        return DecideConceptRequest(
            concept_id=self.validated_data["concept_id"],
            decision=self.validated_data["decision"],
            actor_kind=self.validated_data["actor_kind"],
            actor_id=self.validated_data["actor_id"],
            rationale=self.validated_data["rationale"],
        )


class ConceptCandidateSerializer(serializers.Serializer):
    """Serializer for concept candidate DTO."""

    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    title = serializers.CharField(max_length=500)
    description = serializers.CharField()
    rationale = serializers.CharField()
    rationale_refs = serializers.ListField(child=serializers.UUIDField())
    domain_tags = serializers.ListField(child=serializers.CharField())
    status = serializers.ChoiceField(
        choices=["draft", "proposed", "adopted", "discarded"]
    )
    score = serializers.FloatField(allow_null=True, required=False)
    created_by = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: ConceptCandidateDTO) -> 'ConceptCandidateSerializer':
        """Create serializer from DTO."""
        return cls(data={
            "id": dto.id,
            "session_id": dto.session_id,
            "title": dto.title,
            "description": dto.description,
            "rationale": dto.rationale,
            "rationale_refs": dto.rationale_refs,
            "domain_tags": dto.domain_tags,
            "status": dto.status,
            "score": dto.score,
            "created_by": dto.created_by,
            "created_at": dto.created_at,
            "updated_at": dto.updated_at,
        })


class ConceptDecisionSerializer(serializers.Serializer):
    """Serializer for concept decision DTO."""

    id = serializers.UUIDField()
    concept_id = serializers.UUIDField()
    decision = serializers.ChoiceField(
        choices=["adopt", "hold", "discard", "explore_more"]
    )
    actor_kind = serializers.ChoiceField(choices=["user", "auto"])
    actor_id = serializers.UUIDField()
    rationale = serializers.CharField()
    created_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: ConceptDecisionDTO) -> 'ConceptDecisionSerializer':
        """Create serializer from DTO."""
        return cls(data={
            "id": dto.id,
            "concept_id": dto.concept_id,
            "decision": dto.decision,
            "actor_kind": dto.actor_kind,
            "actor_id": dto.actor_id,
            "rationale": dto.rationale,
            "created_at": dto.created_at,
        })
