"""Django REST serializers for specs module."""
from rest_framework import serializers

from apps.specs.application.dtos import (
    ApproveSpecRequest,
    CreateSpecRequest,
    DomainPackDTO,
    RejectSpecRequest,
    SpecDocumentDTO,
    SpecSectionDTO,
    SubmitForReviewRequest,
    UpdateSectionRequest,
    VersionDiffDTO,
)


class CreateSpecSerializer(serializers.Serializer):
    """Serializer for creating a spec document."""

    session_id = serializers.UUIDField()
    created_by = serializers.UUIDField()

    def to_request_dto(self) -> CreateSpecRequest:
        """Convert to request DTO."""
        return CreateSpecRequest(
            session_id=self.validated_data["session_id"],
            created_by=self.validated_data["created_by"],
        )


class SubmitForReviewSerializer(serializers.Serializer):
    """Serializer for submitting spec for review."""

    spec_id = serializers.UUIDField()
    submitter_id = serializers.UUIDField()

    def to_request_dto(self) -> SubmitForReviewRequest:
        """Convert to request DTO."""
        return SubmitForReviewRequest(
            spec_id=self.validated_data["spec_id"],
            submitter_id=self.validated_data["submitter_id"],
        )


class ApproveSpecSerializer(serializers.Serializer):
    """Serializer for approving a spec."""

    spec_id = serializers.UUIDField()
    approver_id = serializers.UUIDField()
    change_summary = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def to_request_dto(self) -> ApproveSpecRequest:
        """Convert to request DTO."""
        return ApproveSpecRequest(
            spec_id=self.validated_data["spec_id"],
            approver_id=self.validated_data["approver_id"],
            change_summary=self.validated_data.get("change_summary"),
        )


class RejectSpecSerializer(serializers.Serializer):
    """Serializer for rejecting a spec."""

    spec_id = serializers.UUIDField()
    reviewer_id = serializers.UUIDField()
    rejection_reason = serializers.CharField()

    def to_request_dto(self) -> RejectSpecRequest:
        """Convert to request DTO."""
        return RejectSpecRequest(
            spec_id=self.validated_data["spec_id"],
            reviewer_id=self.validated_data["reviewer_id"],
            rejection_reason=self.validated_data["rejection_reason"],
        )


class UpdateSectionSerializer(serializers.Serializer):
    """Serializer for updating a spec section."""

    spec_id = serializers.UUIDField()
    section_type = serializers.CharField()
    content = serializers.DictField()
    evidence_links = serializers.ListField(child=serializers.CharField(), required=False)
    completed = serializers.BooleanField(default=True)

    def to_request_dto(self) -> UpdateSectionRequest:
        """Convert to request DTO."""
        return UpdateSectionRequest(
            spec_id=self.validated_data["spec_id"],
            section_type=self.validated_data["section_type"],
            content=self.validated_data["content"],
            evidence_links=self.validated_data.get("evidence_links"),
            completed=self.validated_data["completed"],
        )


class VersionDiffSerializer(serializers.Serializer):
    """Serializer for version diff."""

    previous_version_id = serializers.CharField()
    new_version_id = serializers.CharField()
    changes = serializers.ListField(child=serializers.CharField())
    changed_sections = serializers.ListField(child=serializers.CharField())
    change_summary = serializers.CharField()

    @classmethod
    def from_dto(cls, dto: VersionDiffDTO) -> "VersionDiffSerializer":
        """Create serializer from DTO."""
        return cls(
            data={
                "previous_version_id": dto.previous_version_id,
                "new_version_id": dto.new_version_id,
                "changes": dto.changes,
                "changed_sections": dto.changed_sections,
                "change_summary": dto.change_summary,
            }
        )


class SpecSectionSerializer(serializers.Serializer):
    """Serializer for spec section."""

    section_type = serializers.CharField()
    title = serializers.CharField()
    content = serializers.DictField()
    evidence_links = serializers.ListField(child=serializers.CharField())
    required = serializers.BooleanField()
    completed = serializers.BooleanField()

    @classmethod
    def from_dto(cls, dto: SpecSectionDTO) -> "SpecSectionSerializer":
        """Create serializer from DTO."""
        return cls(
            data={
                "section_type": dto.section_type,
                "title": dto.title,
                "content": dto.content,
                "evidence_links": dto.evidence_links,
                "required": dto.required,
                "completed": dto.completed,
            }
        )


class SpecDocumentSerializer(serializers.Serializer):
    """Serializer for spec document."""

    id = serializers.UUIDField()
    session_id = serializers.UUIDField()
    domain = serializers.CharField()
    version = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=["draft", "in_review", "approved", "rejected", "superseded"]
    )
    sections = SpecSectionSerializer(many=True)
    evidence_links = serializers.ListField(child=serializers.CharField())
    created_by = serializers.UUIDField()
    approved_by = serializers.UUIDField(allow_null=True, required=False)
    supersedes_id = serializers.UUIDField(allow_null=True, required=False)
    version_diff = VersionDiffSerializer(allow_null=True, required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    @classmethod
    def from_dto(cls, dto: SpecDocumentDTO) -> "SpecDocumentSerializer":
        """Create serializer from DTO."""
        data = {
            "id": dto.id,
            "session_id": dto.session_id,
            "domain": dto.domain,
            "version": dto.version,
            "status": dto.status,
            "sections": [SpecSectionSerializer.from_dto(s).data for s in dto.sections],
            "evidence_links": dto.evidence_links,
            "created_by": dto.created_by,
            "approved_by": dto.approved_by,
            "supersedes_id": dto.supersedes_id,
            "created_at": dto.created_at,
            "updated_at": dto.updated_at,
        }

        if dto.version_diff:
            data["version_diff"] = VersionDiffSerializer.from_dto(dto.version_diff).data

        return cls(data=data)


class DomainPackSerializer(serializers.Serializer):
    """Serializer for domain pack."""

    id = serializers.CharField()
    domain = serializers.CharField()
    brief_schema = serializers.DictField()
    evaluation_axes = serializers.ListField(child=serializers.CharField())
    generation_outputs = serializers.ListField(child=serializers.CharField())
    spec_template_uri = serializers.CharField()
    spec_sections = serializers.ListField(child=serializers.CharField())

    @classmethod
    def from_dto(cls, dto: DomainPackDTO) -> "DomainPackSerializer":
        """Create serializer from DTO."""
        return cls(
            data={
                "id": dto.id,
                "domain": dto.domain,
                "brief_schema": dto.brief_schema,
                "evaluation_axes": dto.evaluation_axes,
                "generation_outputs": dto.generation_outputs,
                "spec_template_uri": dto.spec_template_uri,
                "spec_sections": dto.spec_sections,
            }
        )
