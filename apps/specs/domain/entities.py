"""Domain entities for specs module.

This file is pure Python - no Django imports allowed.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from shared.domain.exceptions import ValidationError

from apps.specs.domain.value_objects import SpecSection, SpecStatus, VersionDiff


# Required section types per REQ-03-SPEC-002
REQUIRED_SECTION_TYPES = [
    "project_brief",
    "trend_evidence",
    "concept_candidates_evaluation",
    "final_concept_decision",
    "user_sketch_original",
    "user_sketch_ai_interpretation",
    "reference_board",
    "abstraction_rules",
    "sketch_and_generated_images",
    "final_comparison",
    "domain_specific_spec",
    "source_license_ai_disclosure",
]


@dataclass
class DomainPack:
    """Domain-specific configuration for spec documents.

    Attributes:
        id: Unique identifier (e.g., "industrial", "fashion")
        domain: Domain name
        brief_schema: JSON schema for brief fields
        evaluation_axes: List of evaluation dimension names
        generation_outputs: List of output types to generate
        spec_template_uri: URI to spec template (DESIGN.md format)
        spec_sections: List of domain-specific section types
    """

    id: str
    domain: str
    brief_schema: dict
    evaluation_axes: list[str]
    generation_outputs: list[str]
    spec_template_uri: str
    spec_sections: list[str]

    def __post_init__(self):
        """Validate domain pack."""
        if not self.id or not self.id.strip():
            raise ValidationError("id", "Domain pack ID cannot be empty")
        if not self.domain or not self.domain.strip():
            raise ValidationError("domain", "Domain name cannot be empty")
        if not isinstance(self.brief_schema, dict):
            raise ValidationError("brief_schema", "Brief schema must be a dictionary")
        if not isinstance(self.evaluation_axes, list) or len(self.evaluation_axes) == 0:
            raise ValidationError("evaluation_axes", "Evaluation axes must be a non-empty list")
        if not isinstance(self.generation_outputs, list) or len(self.generation_outputs) == 0:
            raise ValidationError("generation_outputs", "Generation outputs must be a non-empty list")
        if not self.spec_template_uri or not self.spec_template_uri.strip():
            raise ValidationError("spec_template_uri", "Spec template URI cannot be empty")
        if not isinstance(self.spec_sections, list) or len(self.spec_sections) == 0:
            raise ValidationError("spec_sections", "Spec sections must be a non-empty list")

    def get_brief_fields(self) -> list[str]:
        """Get list of brief field names from schema."""
        return list(self.brief_schema.keys())

    def has_evaluation_axis(self, axis: str) -> bool:
        """Check if domain has a specific evaluation axis."""
        return axis in self.evaluation_axes

    def has_generation_output(self, output_type: str) -> bool:
        """Check if domain supports a specific generation output."""
        return output_type in self.generation_outputs


@dataclass
class SpecDocument:
    """A specification document for design work.

    Attributes:
        id: Unique identifier
        session_id: Associated design session
        domain: Domain identifier (e.g., "industrial", "fashion")
        version: Version number (starts at 1)
        status: Current status
        sections: List of spec sections
        evidence_links: Global traceability links
        created_by: User who created the spec
        approved_by: User who approved (if approved)
        supersedes_id: ID of previous version this supersedes (if any)
        version_diff: Diff metadata if this supersedes another version
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(kw_only=True)
    domain: str = field(kw_only=True)
    version: int = field(default=1, kw_only=True)
    status: SpecStatus = field(default=SpecStatus.DRAFT, kw_only=True)
    sections: list[SpecSection] = field(default_factory=list, kw_only=True)
    evidence_links: list[str] = field(default_factory=list, kw_only=True)
    created_by: UUID = field(kw_only=True)
    approved_by: Optional[UUID] = field(default=None, kw_only=True)
    supersedes_id: Optional[UUID] = field(default=None, kw_only=True)
    version_diff: Optional[VersionDiff] = field(default=None, kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate spec document."""
        if not self.domain or not self.domain.strip():
            raise ValidationError("domain", "Domain cannot be empty")
        if self.version < 1:
            raise ValidationError("version", "Version must be at least 1")
        if self.status == SpecStatus.APPROVED and not self.approved_by:
            raise ValidationError("approved_by", "Approved status requires approved_by user")
        if self.supersedes_id and not self.version_diff:
            raise ValidationError("version_diff", "Superseding requires version diff metadata")

    def transition_to(self, new_status: SpecStatus) -> None:
        """Transition to a new status if valid.

        Args:
            new_status: Target status

        Raises:
            ValidationError: If transition is invalid
        """
        if not self.status.can_transition_to(new_status):
            raise ValidationError(
                "status", f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def add_section(self, section: SpecSection) -> None:
        """Add a section to the spec document.

        Args:
            section: Section to add
        """
        # Check for duplicate section types
        if any(s.section_type == section.section_type for s in self.sections):
            raise ValidationError("section_type", f"Section type {section.section_type} already exists")

        self.sections.append(section)
        self.updated_at = datetime.now(timezone.utc)

    def update_section(self, section_type: str, content: dict, evidence_links: Optional[list[str]] = None) -> None:
        """Update an existing section.

        Args:
            section_type: Type of section to update
            content: New content
            evidence_links: Optional new evidence links

        Raises:
            ValidationError: If section not found
        """
        section = self.get_section(section_type)
        if not section:
            raise ValidationError("section_type", f"Section type {section_type} not found")

        section.content = content
        if evidence_links:
            section.evidence_links = evidence_links
        section.completed = bool(content and content != {})
        self.updated_at = datetime.now(timezone.utc)

    def get_section(self, section_type: str) -> Optional[SpecSection]:
        """Get a section by type.

        Args:
            section_type: Type of section to retrieve

        Returns:
            SpecSection if found, None otherwise
        """
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None

    def add_evidence_link(self, link_id: str) -> None:
        """Add a global evidence link.

        Args:
            link_id: UUID or identifier of evidence source
        """
        if link_id not in self.evidence_links:
            self.evidence_links.append(link_id)
        self.updated_at = datetime.now(timezone.utc)

    def get_required_sections(self) -> list[SpecSection]:
        """Get all required sections.

        Returns:
            List of required SpecSection objects
        """
        return [s for s in self.sections if s.required]

    def get_incomplete_required_sections(self) -> list[SpecSection]:
        """Get all required sections that are not completed.

        Returns:
            List of incomplete required SpecSection objects
        """
        return [s for s in self.sections if s.required and not s.completed]

    def has_all_required_sections(self) -> bool:
        """Check if all required sections exist.

        Returns:
            True if all required section types exist
        """
        existing_types = {s.section_type for s in self.sections}
        required_types = set(REQUIRED_SECTION_TYPES)
        return required_types.issubset(existing_types)

    def has_all_required_sections_complete(self) -> bool:
        """Check if all required sections are complete.

        Returns:
            True if all required sections are completed
        """
        incomplete = self.get_incomplete_required_sections()
        return len(incomplete) == 0

    def mark_approved(self, approved_by: UUID) -> None:
        """Mark the spec as approved.

        Args:
            approved_by: User ID of approver

        Raises:
            ValidationError: If approval prerequisites not met
        """
        # REQ-03-SPEC-004: Cannot approve without all required sections complete
        if not self.has_all_required_sections_complete():
            raise ValidationError(
                "sections", "Cannot approve: all required sections must be complete"
            )

        # REQ-03-SPEC-003: Cannot approve without traceability links
        if not self._has_sufficient_evidence_links():
            raise ValidationError(
                "evidence_links", "Cannot approve: insufficient traceability links"
            )

        self.approved_by = approved_by
        self.transition_to(SpecStatus.APPROVED)

    def _has_sufficient_evidence_links(self) -> bool:
        """Check if there are sufficient evidence links for approval.

        Returns:
            True if sufficient links exist
        """
        # Check global evidence links
        if len(self.evidence_links) == 0:
            return False

        # Check section-specific evidence links for required sections
        required_sections = self.get_required_sections()
        for section in required_sections:
            if section.completed and len(section.evidence_links) == 0:
                return False

        return True

    def create_new_version(self) -> "SpecDocument":
        """Create a new version of this spec document.

        Returns:
            New SpecDocument with incremented version, same session/domain
        """
        return SpecDocument(
            session_id=self.session_id,
            domain=self.domain,
            version=self.version + 1,
            status=SpecStatus.DRAFT,
            created_by=self.created_by,
            supersedes_id=self.id,
        )

    def supersede_with(self, new_version: "SpecDocument", version_diff: VersionDiff) -> None:
        """Mark this spec as superseded by a new version.

        Args:
            new_version: New version spec document
            version_diff: Diff metadata between versions

        Raises:
            ValidationError: If transition is invalid
        """
        if new_version.supersedes_id != self.id:
            raise ValidationError("supersedes_id", "New version must supersede this document")

        self.version_diff = version_diff
        self.transition_to(SpecStatus.SUPERSEDED)
