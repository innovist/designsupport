"""Use case: Generate abstraction rules from a concept.

REQ-03-ABSTRACT-002: One concept must have rules for at least 2 axes.
"""
from typing import Optional
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError, InvariantViolationError

from apps.abstraction.application.dtos import (
    GenerateAbstractionRulesRequest,
    GenerateAbstractionRulesResponse,
    AbstractionRuleDTO,
)
from apps.abstraction.application.ports import (
    AbstractionRuleRepositoryPort,
    ConceptPort,
)
from apps.abstraction.domain.entities import AbstractionRule
from apps.abstraction.domain.services import AbstractionRuleValidator
from apps.abstraction.domain.value_objects import AbstractionAxis, RiskLevel


class GenerateAbstractionRulesUseCase:
    """Generate abstraction rules from a concept candidate.

    This use case analyzes a concept and extracts design rules along
    multiple abstraction axes.
    """

    def __init__(
        self,
        rule_repository: AbstractionRuleRepositoryPort,
        concept_port: ConceptPort,
    ):
        self.rule_repository = rule_repository
        self.concept_port = concept_port

    async def execute(self, request: GenerateAbstractionRulesRequest) -> Result[GenerateAbstractionRulesResponse]:
        """Execute the use case.

        Args:
            request: Request with session_id, concept_id, source_refs

        Returns:
            Result with GenerateAbstractionRulesResponse or error
        """
        # Validate concept exists
        concept = await self.concept_port.get_by_id(request.concept_id)
        if not concept:
            return Result.failure(
                NotFoundError("Concept", str(request.concept_id))
            )

        # Generate rules for all axes
        generated_rules = []
        rejected_count = 0

        for axis in AbstractionAxis.all_axes():
            # Generate observation and applied rule based on concept
            # In production, this would use AI/LLM to analyze the concept
            observation, applied_rule = self._generate_rule_for_axis(
                axis, concept, request.source_refs
            )

            # Create rule
            rule = AbstractionRule(
                session_id=request.session_id,
                concept_id=request.concept_id,
                axis=axis,
                observation=observation,
                applied_rule=applied_rule,
                source_refs=request.source_refs,
            )

            # Determine license risk from concept metadata
            # REQ-03-ABSTRACT-005: Check license risk from reference sources
            license_risk = self._determine_license_risk(concept)

            # Validate rule for safety
            is_valid, risk_reason = AbstractionRuleValidator.validate_rule(
                rule,
                license_risk=license_risk
            )

            # If license risk is high, mark rule as risky
            if license_risk == RiskLevel.HIGH:
                rule.mark_risky(
                    reason=f"High license risk from reference source: {concept.get('license_level', 'unknown')}"
                )

            if is_valid:
                # Save valid rule
                saved_rule = await self.rule_repository.save(rule)
                generated_rules.append(saved_rule)
            else:
                rejected_count += 1
                # Log or record the rejection for audit purposes

        # REQ-03-ABSTRACT-002: At least 2 axes must have valid rules
        if len(generated_rules) < 2:
            return Result.failure(
                InvariantViolationError(
                    "minimum_axes",
                    "At least 2 abstraction axes must have valid rules"
                )
            )

        # Convert to DTOs
        rule_dtos = [
            AbstractionRuleDTO(
                id=rule.id,
                session_id=rule.session_id,
                concept_id=rule.concept_id,
                axis=rule.axis.value,
                observation=rule.observation,
                applied_rule=rule.applied_rule,
                source_refs=rule.source_refs,
                risk_note=rule.risk_note,
                created_at=rule.created_at,
            )
            for rule in generated_rules
        ]

        response = GenerateAbstractionRulesResponse(
            rules=rule_dtos,
            rejected_count=rejected_count,
        )

        return Result.success(response)

    def _generate_rule_for_axis(
        self,
        axis: AbstractionAxis,
        concept: dict,
        source_refs: list[UUID],
    ) -> tuple[str, str]:
        """Generate observation and applied rule for a specific axis.

        In production, this would use AI/LLM to analyze the concept description
        and extract relevant design principles.

        Args:
            axis: Abstraction axis
            concept: Concept data
            source_refs: Source references

        Returns:
            Tuple of (observation, applied_rule)
        """
        # Simplified implementation - production would use LLM
        concept_desc = concept.get("description", "")
        concept_rationale = concept.get("rationale", "")

        axis_templates = {
            AbstractionAxis.FORM: (
                f"Observed formal qualities in: {concept_desc[:100]}",
                f"Apply geometric simplification and organic form balance inspired by the concept's formal structure"
            ),
            AbstractionAxis.STRUCTURE: (
                f"Observed structural organization in: {concept_desc[:100]}",
                f"Maintain hierarchical information architecture with clear visual grouping"
            ),
            AbstractionAxis.SURFACE: (
                f"Observed surface treatment in: {concept_desc[:100]}",
                f"Balance texture contrast with smooth surfaces for tactile and visual interest"
            ),
            AbstractionAxis.COLOR_MATERIAL: (
                f"Observed color and material choices in: {concept_desc[:100]}",
                f"Use complementary color palette with natural material finishes"
            ),
            AbstractionAxis.MEANING: (
                f"Observed semantic meaning in: {concept_rationale[:100]}",
                f"Communicate core concept through symbolic visual language"
            ),
            AbstractionAxis.USABILITY: (
                f"Observed usability considerations in: {concept_desc[:100]}",
                f"Prioritize intuitive interaction patterns and cognitive ease"
            ),
        }

        return axis_templates.get(axis, axis_templates[AbstractionAxis.FORM])

    def _determine_license_risk(self, concept: dict) -> RiskLevel:
        """Determine license risk from concept metadata.

        REQ-03-ABSTRACT-005: Check license risk from reference sources.

        Args:
            concept: Concept data dictionary

        Returns:
            RiskLevel based on concept metadata
        """
        # Check license_level from concept metadata
        license_level = concept.get("license_level", "").lower()

        # High risk: tier 3 or explicit high license level
        if license_level == "high" or license_level == "tier_3" or license_level == "3":
            return RiskLevel.HIGH

        # Medium risk: tier 2 or medium license level
        if license_level == "medium" or license_level == "tier_2" or license_level == "2":
            return RiskLevel.MEDIUM

        # Low risk: tier 1 or low license level
        if license_level == "low" or license_level == "tier_1" or license_level == "1":
            return RiskLevel.LOW

        # Unknown: no license information available
        return RiskLevel.UNKNOWN

