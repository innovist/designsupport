"""Domain services for specs module.

This file is pure Python - no Django imports allowed.
"""
from typing import Optional

from shared.domain.exceptions import ValidationError

from apps.specs.domain.entities import DomainPack, SpecDocument
from apps.specs.domain.value_objects import SpecStatus, VersionDiff


# @MX:ANCHOR: SpecDocumentValidator validates spec completeness before approval
# @MX:REASON: REQ-03-SPEC-004 requires all sections + traceability + decision logs for approval
class SpecDocumentValidator:
    """Service for validating spec documents before approval.

    Enforces REQ-03-SPEC-002, REQ-03-SPEC-003, REQ-03-SPEC-004 requirements.
    """

    @staticmethod
    def validate_for_approval(spec: SpecDocument) -> None:
        """Validate that a spec document can be approved.

        Args:
            spec: Spec document to validate

        Raises:
            ValidationError: If validation fails
        """
        # Check status is in_review
        if spec.status != SpecStatus.IN_REVIEW:
            raise ValidationError(
                "status", f"Cannot approve spec with status {spec.status.value}. Must be in_review."
            )

        # Check all required sections exist and are complete
        SpecDocumentValidator._validate_required_sections(spec)

        # Check traceability links
        SpecDocumentValidator._validate_traceability_links(spec)

        # Check decision logs exist (if concepts were evaluated)
        SpecDocumentValidator._validate_decision_logs(spec)

    @staticmethod
    def _validate_required_sections(spec: SpecDocument) -> None:
        """Validate all required sections exist and are complete.

        Args:
            spec: Spec document to validate

        Raises:
            ValidationError: If sections missing or incomplete
        """
        from apps.specs.domain.entities import REQUIRED_SECTION_TYPES

        missing_sections = []
        incomplete_sections = []

        for section_type in REQUIRED_SECTION_TYPES:
            section = spec.get_section(section_type)
            if not section:
                missing_sections.append(section_type)
            elif section.required and not section.completed:
                incomplete_sections.append(section_type)

        if missing_sections:
            raise ValidationError(
                "sections",
                f"Missing required sections: {', '.join(missing_sections)}"
            )

        if incomplete_sections:
            raise ValidationError(
                "sections",
                f"Incomplete required sections: {', '.join(incomplete_sections)}"
            )

    @staticmethod
    def _validate_traceability_links(spec: SpecDocument) -> None:
        """Validate sufficient traceability links exist.

        Enforces REQ-03-SPEC-003: All sections must cite sources.

        Args:
            spec: Spec document to validate

        Raises:
            ValidationError: If insufficient links
        """
        # Check global evidence links
        if len(spec.evidence_links) == 0:
            raise ValidationError(
                "evidence_links",
                "Spec must have global traceability links to sources, decisions, or generation jobs"
            )

        # Check section-specific evidence links
        required_sections = spec.get_required_sections()
        sections_without_links = []

        for section in required_sections:
            if section.completed and len(section.evidence_links) == 0:
                sections_without_links.append(section.section_type)

        if sections_without_links:
            raise ValidationError(
                "evidence_links",
                f"Sections missing traceability links: {', '.join(sections_without_links)}"
            )

    @staticmethod
    def _validate_decision_logs(spec: SpecDocument) -> None:
        """Validate that concept decisions are documented.

        Enforces REQ-03-SPEC-005: Discarded/hold concepts preserved.

        Args:
            spec: Spec document to validate

        Raises:
            ValidationError: If decision logs missing
        """
        # Check if concept_candidates_evaluation section exists
        evaluation_section = spec.get_section("concept_candidates_evaluation")
        if evaluation_section and evaluation_section.completed:
            content = evaluation_section.content

            # Check for decision logs in content
            if "decision_logs" not in content or not content["decision_logs"]:
                raise ValidationError(
                    "concept_candidates_evaluation",
                    "Concept evaluation section must include decision logs for all candidates"
                )

            # Check that discarded/hold concepts are documented
            if "discarded_concepts" not in content or "held_concepts" not in content:
                raise ValidationError(
                    "concept_candidates_evaluation",
                    "Decision logs must document discarded and held concepts per REQ-03-SPEC-005"
                )


# @MX:ANCHOR: SpecVersionManager handles version transitions and superseding logic
# @MX:REASON: REQ-03-SPEC-004 requires automatic superseding with diff metadata when new version approved
class SpecVersionManager:
    """Service for managing spec document versioning and superseding."""

    @staticmethod
    def create_version_diff(old_spec: SpecDocument, new_spec: SpecDocument, change_summary: str) -> VersionDiff:
        """Create version diff between two spec versions.

        Args:
            old_spec: Previous version
            new_spec: New version
            change_summary: Human-readable summary of changes

        Returns:
            VersionDiff with change metadata
        """
        changes = []
        changed_sections = []

        # Compare sections
        old_section_types = {s.section_type for s in old_spec.sections}
        new_section_types = {s.section_type for s in new_spec.sections}

        # Added sections
        added = new_section_types - old_section_types
        if added:
            changes.append(f"Added sections: {', '.join(added)}")
            changed_sections.extend(added)

        # Removed sections (shouldn't happen in practice)
        removed = old_section_types - new_section_types
        if removed:
            changes.append(f"Removed sections: {', '.join(removed)}")
            changed_sections.extend(removed)

        # Modified sections
        for old_section in old_spec.sections:
            if old_section.section_type in new_section_types:
                new_section = new_spec.get_section(old_section.section_type)
                if new_section and old_section.content != new_section.content:
                    changes.append(f"Modified section: {old_section.section_type}")
                    changed_sections.append(old_section.section_type)

        return VersionDiff(
            previous_version_id=str(old_spec.id),
            new_version_id=str(new_spec.id),
            changes=changes,
            changed_sections=list(set(changed_sections)),
            change_summary=change_summary,
        )

    @staticmethod
    def handle_new_version_approval(old_spec: SpecDocument, new_spec: SpecDocument, change_summary: str) -> None:
        """Handle approval of new version by superseding old version.

        Enforces REQ-03-SPEC-004: Previous version becomes superseded with diff metadata.

        Args:
            old_spec: Previous version to supersede
            new_spec: New version being approved
            change_summary: Summary of changes
        """
        # Create version diff
        version_diff = SpecVersionManager.create_version_diff(old_spec, new_spec, change_summary)

        # Mark old version as superseded
        old_spec.supersede_with(new_spec, version_diff)


# @MX:ANCHOR: DomainPackResolver resolves domain-specific fields from DomainPack data
# @MX:REASON: INV-03-03 requires NO hardcoded if/elif domain branches - all behavior driven by data
class DomainPackResolver:
    """Service for resolving domain-specific behavior from DomainPack data.

    Enforces INV-03-03: No hardcoded domain string branches in code.
    """

    @staticmethod
    def get_brief_schema(domain_pack: DomainPack) -> dict:
        """Get brief schema for a domain.

        Args:
            domain_pack: Domain pack configuration

        Returns:
            Brief schema dictionary
        """
        return domain_pack.brief_schema

    @staticmethod
    def get_evaluation_axes(domain_pack: DomainPack) -> list[str]:
        """Get evaluation axes for a domain.

        Args:
            domain_pack: Domain pack configuration

        Returns:
            List of evaluation axis names
        """
        return domain_pack.evaluation_axes

    @staticmethod
    def get_generation_outputs(domain_pack: DomainPack) -> list[str]:
        """Get generation outputs for a domain.

        Args:
            domain_pack: Domain pack configuration

        Returns:
            List of generation output types
        """
        return domain_pack.generation_outputs

    @staticmethod
    def get_spec_sections(domain_pack: DomainPack) -> list[str]:
        """Get domain-specific spec sections.

        Args:
            domain_pack: Domain pack configuration

        Returns:
            List of section types
        """
        return domain_pack.spec_sections

    @staticmethod
    def resolve_section_content(domain_pack: DomainPack, section_type: str, brief_data: dict) -> dict:
        """Resolve section content structure based on domain pack.

        Args:
            domain_pack: Domain pack configuration
            section_type: Type of section to resolve
            brief_data: Brief data to extract from

        Returns:
            Section content structure
        """
        # Map section types to brief fields
        section_field_map = {
            "project_brief": "brief_data",
            "trend_evidence": "trend_insights",
            "concept_candidates_evaluation": "concepts",
            "final_concept_decision": "selected_concept",
            # Other sections are domain-specific
        }

        if section_type in section_field_map:
            field_name = section_field_map[section_type]
            return {field_name: brief_data.get(field_name, {})}

        # For domain-specific sections, check spec_sections
        if section_type in domain_pack.spec_sections:
            # Return empty template - will be filled by application layer
            return {"domain": domain_pack.domain, "section_type": section_type}

        # Unknown section type
        return {}

    @staticmethod
    def validate_brief_for_domain(domain_pack: DomainPack, brief_data: dict) -> None:
        """Validate that brief data matches domain schema.

        Args:
            domain_pack: Domain pack configuration
            brief_data: Brief data to validate

        Raises:
            ValidationError: If brief doesn't match schema
        """
        required_fields = domain_pack.get_brief_fields()
        missing_fields = []

        for field in required_fields:
            if field not in brief_data:
                missing_fields.append(field)

        if missing_fields:
            raise ValidationError(
                "brief_data",
                f"Missing required fields for domain {domain_pack.domain}: {', '.join(missing_fields)}"
            )
