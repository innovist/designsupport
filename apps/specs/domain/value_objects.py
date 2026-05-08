"""Value objects for specs module.

This file is pure Python - no Django imports allowed.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from shared.domain.exceptions import ValidationError


class SpecStatus(str, Enum):
    """Status of a spec document."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"

    def can_transition_to(self, target: "SpecStatus") -> bool:
        """Check if state transition is valid."""
        transitions = {
            SpecStatus.DRAFT: [SpecStatus.IN_REVIEW, SpecStatus.REJECTED],
            SpecStatus.IN_REVIEW: [SpecStatus.APPROVED, SpecStatus.REJECTED],
            SpecStatus.APPROVED: [SpecStatus.SUPERSEDED],
            SpecStatus.REJECTED: [SpecStatus.DRAFT],  # Can resubmit
            SpecStatus.SUPERSEDED: [],  # Terminal state
        }
        return target in transitions.get(self, [])


@dataclass
class SpecSection:
    """A section within a spec document.

    Attributes:
        section_type: Type of section (e.g., "project_brief", "trend_evidence")
        title: Section title
        content: Section content (can be structured data)
        evidence_links: List of traceability links (UUIDs to sources, jobs, decisions)
        required: Whether this section is required for approval
        completed: Whether this section has been filled out
    """

    section_type: str
    title: str
    content: dict
    evidence_links: list[str]
    required: bool
    completed: bool = False

    def __post_init__(self):
        """Validate spec section."""
        if not self.section_type or not self.section_type.strip():
            raise ValidationError("section_type", "Section type cannot be empty")
        if not self.title or not self.title.strip():
            raise ValidationError("title", "Section title cannot be empty")
        if not isinstance(self.content, dict):
            raise ValidationError("content", "Section content must be a dictionary")
        if not isinstance(self.evidence_links, list):
            raise ValidationError("evidence_links", "Evidence links must be a list")

    def mark_complete(self, evidence_links: Optional[list[str]] = None) -> None:
        """Mark section as complete with optional evidence links.

        Args:
            evidence_links: Optional additional evidence links to add
        """
        self.completed = True
        if evidence_links:
            self.evidence_links.extend(evidence_links)

    def add_evidence_link(self, link_id: str) -> None:
        """Add an evidence link to this section.

        Args:
            link_id: UUID or identifier of the evidence source
        """
        if link_id not in self.evidence_links:
            self.evidence_links.append(link_id)


@dataclass
class VersionDiff:
    """Diff metadata for superseded spec versions.

    Attributes:
        previous_version_id: ID of the previous version
        new_version_id: ID of the new version
        changes: List of change descriptions
        changed_sections: List of section types that changed
        change_summary: Brief summary of changes
    """

    previous_version_id: str
    new_version_id: str
    changes: list[str]
    changed_sections: list[str]
    change_summary: str

    def __post_init__(self):
        """Validate version diff."""
        if not self.previous_version_id:
            raise ValidationError("previous_version_id", "Previous version ID cannot be empty")
        if not self.new_version_id:
            raise ValidationError("new_version_id", "New version ID cannot be empty")
        if not isinstance(self.changes, list):
            raise ValidationError("changes", "Changes must be a list")
        if not isinstance(self.changed_sections, list):
            raise ValidationError("changed_sections", "Changed sections must be a list")
        if not self.change_summary or not self.change_summary.strip():
            raise ValidationError("change_summary", "Change summary cannot be empty")
