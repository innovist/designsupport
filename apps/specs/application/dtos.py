"""Data Transfer Objects for specs module."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class DomainPackDTO:
    """DTO for domain pack."""

    id: str
    domain: str
    brief_schema: dict
    evaluation_axes: list[str]
    generation_outputs: list[str]
    spec_template_uri: str
    spec_sections: list[str]

    @classmethod
    def from_entity(cls, pack) -> "DomainPackDTO":
        """Create DTO from domain entity."""
        return cls(
            id=pack.id,
            domain=pack.domain,
            brief_schema=pack.brief_schema,
            evaluation_axes=pack.evaluation_axes,
            generation_outputs=pack.generation_outputs,
            spec_template_uri=pack.spec_template_uri,
            spec_sections=pack.spec_sections,
        )


@dataclass
class SpecSectionDTO:
    """DTO for spec section."""

    section_type: str
    title: str
    content: dict
    evidence_links: list[str]
    required: bool
    completed: bool

    @classmethod
    def from_value_object(cls, section) -> "SpecSectionDTO":
        """Create DTO from value object."""
        return cls(
            section_type=section.section_type,
            title=section.title,
            content=section.content,
            evidence_links=section.evidence_links,
            required=section.required,
            completed=section.completed,
        )


@dataclass
class VersionDiffDTO:
    """DTO for version diff."""

    previous_version_id: str
    new_version_id: str
    changes: list[str]
    changed_sections: list[str]
    change_summary: str

    @classmethod
    def from_value_object(cls, diff) -> "VersionDiffDTO":
        """Create DTO from value object."""
        return cls(
            previous_version_id=diff.previous_version_id,
            new_version_id=diff.new_version_id,
            changes=diff.changes,
            changed_sections=diff.changed_sections,
            change_summary=diff.change_summary,
        )


@dataclass
class SpecDocumentDTO:
    """DTO for spec document."""

    id: UUID
    session_id: UUID
    domain: str
    version: int
    status: str
    sections: list[SpecSectionDTO]
    evidence_links: list[str]
    created_by: UUID
    approved_by: Optional[UUID]
    supersedes_id: Optional[UUID]
    version_diff: Optional[VersionDiffDTO]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, spec) -> "SpecDocumentDTO":
        """Create DTO from domain entity."""
        return cls(
            id=spec.id,
            session_id=spec.session_id,
            domain=spec.domain,
            version=spec.version,
            status=spec.status.value,
            sections=[SpecSectionDTO.from_value_object(s) for s in spec.sections],
            evidence_links=spec.evidence_links,
            created_by=spec.created_by,
            approved_by=spec.approved_by,
            supersedes_id=spec.supersedes_id,
            version_diff=VersionDiffDTO.from_value_object(spec.version_diff) if spec.version_diff else None,
            created_at=spec.created_at,
            updated_at=spec.updated_at,
        )


@dataclass
class CreateSpecRequest:
    """Request DTO for creating a spec document."""

    session_id: UUID
    created_by: UUID


@dataclass
class SubmitForReviewRequest:
    """Request DTO for submitting spec for review."""

    spec_id: UUID
    submitter_id: UUID


@dataclass
class ApproveSpecRequest:
    """Request DTO for approving a spec."""

    spec_id: UUID
    approver_id: UUID
    change_summary: Optional[str] = None  # Required if superseding previous version


@dataclass
class RejectSpecRequest:
    """Request DTO for rejecting a spec."""

    spec_id: UUID
    reviewer_id: UUID
    rejection_reason: str


@dataclass
class UpdateSectionRequest:
    """Request DTO for updating a spec section."""

    spec_id: UUID
    section_type: str
    content: dict
    evidence_links: Optional[list[str]] = None
    completed: bool = True


@dataclass
class AddEvidenceLinkRequest:
    """Request DTO for adding evidence links."""

    spec_id: UUID
    link_id: str
    section_type: Optional[str] = None  # If None, adds to global links


@dataclass
class VersionSpecRequest:
    """Request DTO for creating a new version of a spec.

    REQ-03-SPEC-006: Version control with superseding
    """

    spec_id: UUID
    created_by: UUID
    version_diff: Optional[VersionDiffDTO] = None  # Optional diff metadata
