"""Django ORM models for specs module."""
from django.db import models

from shared.infrastructure.orm.base_model import TimestampedModel


class DomainPackModel(models.Model):
    """Django model for DomainPack entity.

    Stored as data (not code) per REQ-03-DOMAIN-001.
    """

    id = models.CharField(primary_key=True, max_length=50)  # e.g., "industrial", "fashion"
    domain = models.CharField(max_length=100, unique=True)
    brief_schema = models.JSONField(default=dict)  # JSON schema for brief fields
    evaluation_axes = models.JSONField(default=list)  # List of axis names
    generation_outputs = models.JSONField(default=list)  # List of output types
    spec_template_uri = models.CharField(max_length=500)  # URI to template
    spec_sections = models.JSONField(default=list)  # List of domain-specific section types
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "domain_packs"
        verbose_name = "Domain Pack"
        verbose_name_plural = "Domain Packs"

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.specs.domain.entities import DomainPack

        return DomainPack(
            id=self.id,
            domain=self.domain,
            brief_schema=self.brief_schema,
            evaluation_axes=self.evaluation_axes,
            generation_outputs=self.generation_outputs,
            spec_template_uri=self.spec_template_uri,
            spec_sections=self.spec_sections,
        )

    @classmethod
    def from_domain(cls, pack):
        """Create ORM model from domain entity."""
        return cls(
            id=pack.id,
            domain=pack.domain,
            brief_schema=pack.brief_schema,
            evaluation_axes=pack.evaluation_axes,
            generation_outputs=pack.generation_outputs,
            spec_template_uri=pack.spec_template_uri,
            spec_sections=pack.spec_sections,
        )


class SpecDocumentModel(TimestampedModel):
    """Django model for SpecDocument entity."""

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    domain = models.CharField(max_length=50, db_index=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("in_review", "In Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("superseded", "Superseded"),
        ],
        default="draft",
        db_index=True,
    )
    sections = models.JSONField(default=list)  # List of section dicts
    evidence_links = models.JSONField(default=list)  # List of link IDs
    created_by = models.UUIDField(db_index=True)
    approved_by = models.UUIDField(null=True, blank=True, db_index=True)
    supersedes_id = models.UUIDField(null=True, blank=True, db_index=True)
    version_diff = models.JSONField(null=True, blank=True)  # VersionDiff dict

    class Meta:
        db_table = "spec_documents"
        verbose_name = "Spec Document"
        verbose_name_plural = "Spec Documents"
        indexes = [
            models.Index(fields=["session_id", "-version"]),
            models.Index(fields=["status"]),
            models.Index(fields=["domain"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["supersedes_id"]),
        ]
        ordering = ["-version"]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.specs.domain.entities import SpecDocument, SpecSection, SpecStatus
        from apps.specs.domain.value_objects import VersionDiff
        from uuid import UUID

        # Convert sections from dicts to SpecSection objects
        sections = []
        for section_dict in self.sections:
            sections.append(
                SpecSection(
                    section_type=section_dict["section_type"],
                    title=section_dict["title"],
                    content=section_dict["content"],
                    evidence_links=section_dict["evidence_links"],
                    required=section_dict["required"],
                    completed=section_dict["completed"],
                )
            )

        # Convert version_diff from dict to VersionDiff object
        version_diff = None
        if self.version_diff:
            version_diff = VersionDiff(
                previous_version_id=self.version_diff["previous_version_id"],
                new_version_id=self.version_diff["new_version_id"],
                changes=self.version_diff["changes"],
                changed_sections=self.version_diff["changed_sections"],
                change_summary=self.version_diff["change_summary"],
            )

        return SpecDocument(
            id=UUID(str(self.id)),
            session_id=UUID(str(self.session_id)),
            domain=self.domain,
            version=self.version,
            status=SpecStatus(self.status),
            sections=sections,
            evidence_links=self.evidence_links,
            created_by=UUID(str(self.created_by)),
            approved_by=UUID(str(self.approved_by)) if self.approved_by else None,
            supersedes_id=UUID(str(self.supersedes_id)) if self.supersedes_id else None,
            version_diff=version_diff,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, spec):
        """Create ORM model from domain entity."""
        # Convert sections from SpecSection objects to dicts
        sections_dict = []
        for section in spec.sections:
            sections_dict.append(
                {
                    "section_type": section.section_type,
                    "title": section.title,
                    "content": section.content,
                    "evidence_links": section.evidence_links,
                    "required": section.required,
                    "completed": section.completed,
                }
            )

        # Convert version_diff from VersionDiff object to dict
        version_diff_dict = None
        if spec.version_diff:
            version_diff_dict = {
                "previous_version_id": spec.version_diff.previous_version_id,
                "new_version_id": spec.version_diff.new_version_id,
                "changes": spec.version_diff.changes,
                "changed_sections": spec.version_diff.changed_sections,
                "change_summary": spec.version_diff.change_summary,
            }

        return cls(
            id=str(spec.id),
            session_id=str(spec.session_id),
            domain=spec.domain,
            version=spec.version,
            status=spec.status.value,
            sections=sections_dict,
            evidence_links=spec.evidence_links,
            created_by=str(spec.created_by),
            approved_by=str(spec.approved_by) if spec.approved_by else None,
            supersedes_id=str(spec.supersedes_id) if spec.supersedes_id else None,
            version_diff=version_diff_dict,
            created_at=spec.created_at,
            updated_at=spec.updated_at,
        )
