"""DRF serializers for generation module."""
from rest_framework import serializers

from apps.generation.application.dtos import (
    CreateGenerationJobRequest,
    GenerationJobResponse,
    GeneratedDesignResponse,
    ExecuteJobRequest,
    ExecuteJobResponse
)
from apps.generation.domain.value_objects import GenerationStatus, GenerationKind, AssetKind


class GenerationStatusSerializer(serializers.Field):
    """Serializer for GenerationStatus enum."""

    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        try:
            return GenerationStatus(data)
        except ValueError:
            raise serializers.ValidationError(f"Invalid status: {data}")


class GenerationKindSerializer(serializers.Field):
    """Serializer for GenerationKind enum."""

    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        try:
            return GenerationKind(data)
        except ValueError:
            raise serializers.ValidationError(f"Invalid kind: {data}")


class AssetKindSerializer(serializers.Field):
    """Serializer for AssetKind enum."""

    def to_representation(self, obj):
        return obj.value

    def to_internal_value(self, data):
        try:
            return AssetKind(data)
        except ValueError:
            raise serializers.ValidationError(f"Invalid asset kind: {data}")


class CreateGenerationJobSerializer(serializers.Serializer):
    """Serializer for creating a generation job."""
    session_id = serializers.UUIDField()
    kind = GenerationKindSerializer()
    prompt_id = serializers.UUIDField(required=False, allow_null=True)
    brief_id = serializers.UUIDField(required=False, allow_null=True)
    concept_id = serializers.UUIDField(required=False, allow_null=True)
    rule_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=[]
    )
    sketch_id = serializers.UUIDField(required=False, allow_null=True)
    reference_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=[]
    )
    model_policy_key = serializers.CharField(default="default")

    def to_request(self) -> CreateGenerationJobRequest:
        """Convert to DTO.

        Returns:
            CreateGenerationJobRequest
        """
        return CreateGenerationJobRequest(
            session_id=self.validated_data["session_id"],
            kind=self.validated_data["kind"],
            prompt_id=self.validated_data.get("prompt_id"),
            brief_id=self.validated_data.get("brief_id"),
            concept_id=self.validated_data.get("concept_id"),
            rule_ids=self.validated_data.get("rule_ids", []),
            sketch_id=self.validated_data.get("sketch_id"),
            reference_ids=self.validated_data.get("reference_ids", []),
            model_policy_key=self.validated_data.get("model_policy_key", "default")
        )


class GenerationJobSerializer(serializers.Serializer):
    """Serializer for GenerationJobResponse."""
    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    kind = GenerationKindSerializer()
    prompt_id = serializers.UUIDField(allow_null=True)
    brief_id = serializers.UUIDField(allow_null=True)
    concept_id = serializers.UUIDField(allow_null=True)
    rule_ids = serializers.ListField(child=serializers.UUIDField())
    sketch_id = serializers.UUIDField(allow_null=True)
    reference_ids = serializers.ListField(child=serializers.UUIDField())
    status = GenerationStatusSerializer()
    model_policy_key = serializers.CharField()
    retries = serializers.IntegerField()
    error_message = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)

    @classmethod
    def from_response(cls, response: GenerationJobResponse):
        """Create from DTO.

        Args:
            response: GenerationJobResponse

        Returns:
            Serialized data
        """
        return cls({
            "id": response.id,
            "session_id": response.session_id,
            "kind": response.kind,
            "prompt_id": response.prompt_id,
            "brief_id": response.brief_id,
            "concept_id": response.concept_id,
            "rule_ids": response.rule_ids,
            "sketch_id": response.sketch_id,
            "reference_ids": response.reference_ids,
            "status": response.status,
            "model_policy_key": response.model_policy_key,
            "retries": response.retries,
            "error_message": response.error_message,
            "created_at": response.created_at,
            "updated_at": response.updated_at,
            "completed_at": response.completed_at
        }).data


class GeneratedDesignSerializer(serializers.Serializer):
    """Serializer for GeneratedDesignResponse."""
    id = serializers.UUIDField()
    job_id = serializers.UUIDField()
    asset_uri = serializers.CharField()
    asset_kind = AssetKindSerializer()
    parent_sketch_id = serializers.UUIDField(allow_null=True)
    brief_id = serializers.UUIDField(allow_null=True)
    concept_id = serializers.UUIDField(allow_null=True)
    rule_ids = serializers.ListField(child=serializers.UUIDField())
    reference_ids = serializers.ListField(child=serializers.UUIDField())
    model_policy_key = serializers.CharField()
    prompt_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()

    @classmethod
    def from_response(cls, response: GeneratedDesignResponse):
        """Create from DTO.

        Args:
            response: GeneratedDesignResponse

        Returns:
            Serialized data
        """
        return cls({
            "id": response.id,
            "job_id": response.job_id,
            "asset_uri": response.asset_uri,
            "asset_kind": response.asset_kind,
            "parent_sketch_id": response.parent_sketch_id,
            "brief_id": response.brief_id,
            "concept_id": response.concept_id,
            "rule_ids": response.rule_ids,
            "reference_ids": response.reference_ids,
            "model_policy_key": response.model_policy_key,
            "prompt_id": response.prompt_id,
            "created_at": response.created_at
        }).data


class ExecuteJobSerializer(serializers.Serializer):
    """Serializer for executing a generation job."""
    job_id = serializers.UUIDField()
    force_retry = serializers.BooleanField(default=False)

    def to_request(self) -> ExecuteJobRequest:
        """Convert to DTO.

        Returns:
            ExecuteJobRequest
        """
        return ExecuteJobRequest(
            job_id=self.validated_data["job_id"],
            force_retry=self.validated_data.get("force_retry", False)
        )


class ExecuteJobResponseSerializer(serializers.Serializer):
    """Serializer for ExecuteJobResponse."""
    job_id = serializers.UUIDField()
    status = GenerationStatusSerializer()
    design_ids = serializers.ListField(child=serializers.UUIDField())
    asset_uris = serializers.ListField(child=serializers.CharField())
    cost_metadata = serializers.DictField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)

    @classmethod
    def from_response(cls, response: ExecuteJobResponse):
        """Create from DTO.

        Args:
            response: ExecuteJobResponse

        Returns:
            Serialized data
        """
        return cls({
            "job_id": response.job_id,
            "status": response.status,
            "design_ids": response.design_ids,
            "asset_uris": response.asset_uris,
            "cost_metadata": response.cost_metadata,
            "error_message": response.error_message
        }).data
