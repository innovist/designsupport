"""Use case: Validate prompt safety.

REQ-03-PROMPT-006: Record safety violations for auditing.
"""
from typing import Optional
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import ValidationError

from apps.abstraction.application.dtos import (
    ValidatePromptSafetyRequest,
    ValidatePromptSafetyResponse,
    PromptSafetyViolationDTO,
)
from apps.abstraction.application.ports import (
    PromptSafetyViolationRepositoryPort,
    PromptPatternRepositoryPort,
)
from apps.abstraction.domain.entities import PromptSafetyViolation
from apps.abstraction.domain.services import AbstractionRuleValidator
from apps.abstraction.domain.value_objects import RiskLevel


class ValidatePromptSafetyUseCase:
    """Validate prompt safety against rules.

    This use case checks prompts against safety rules and records violations.
    """

    def __init__(
        self,
        violation_repository: PromptSafetyViolationRepositoryPort,
        pattern_repository: PromptPatternRepositoryPort,
    ):
        self.violation_repository = violation_repository
        self.pattern_repository = pattern_repository

    async def execute(self, request: ValidatePromptSafetyRequest) -> Result[ValidatePromptSafetyResponse]:
        """Execute the use case.

        Args:
            request: Request with session_id, prompt_id, prompt_text, source_refs

        Returns:
            Result with ValidatePromptSafetyResponse or error
        """
        if not request.prompt_text or not request.prompt_text.strip():
            return Result.failure(
                ValidationError("prompt_text", "Prompt text cannot be empty")
            )

        violations = []

        # Check against brand/style mimicry patterns
        mimicry_violations = self._check_mimicry_violations(request)
        violations.extend(mimicry_violations)

        # Check against license risk patterns
        license_violations = self._check_license_violations(request)
        violations.extend(license_violations)

        # Check against active prompt pattern safety rules
        pattern_violations = await self._check_pattern_violations(request)
        violations.extend(pattern_violations)

        # Save all violations
        saved_violations = []
        for violation in violations:
            saved = await self.violation_repository.save(violation)
            saved_violations.append(saved)

        # Convert to DTOs
        violation_dtos = [
            PromptSafetyViolationDTO(
                id=v.id,
                session_id=v.session_id,
                prompt_id=v.prompt_id,
                reason=v.reason,
                source_refs=v.source_refs,
                created_at=v.created_at,
            )
            for v in saved_violations
        ]

        is_safe = len(violation_dtos) == 0

        response = ValidatePromptSafetyResponse(
            is_safe=is_safe,
            violations=violation_dtos,
        )

        return Result.success(response)

    def _check_mimicry_violations(self, request: ValidatePromptSafetyRequest) -> list[PromptSafetyViolation]:
        """Check for brand/style mimicry violations."""
        violations = []

        # Use the validator from domain services
        is_safe, reason = AbstractionRuleValidator._check_brand_mimicry(
            type('obj', (object,), {
                'observation': request.prompt_text,
                'applied_rule': request.prompt_text,
            })
        )

        if reason:
            violation = PromptSafetyViolation(
                session_id=request.session_id,
                prompt_id=request.prompt_id,
                reason=reason,
                source_refs=request.source_refs,
            )
            violations.append(violation)

        return violations

    def _check_license_violations(self, request: ValidatePromptSafetyRequest) -> list[PromptSafetyViolation]:
        """Check for license risk violations."""
        violations = []

        is_safe, reason = AbstractionRuleValidator._check_license_risk(
            type('obj', (object,), {
                'observation': request.prompt_text,
                'applied_rule': request.prompt_text,
            })
        )

        if reason:
            violation = PromptSafetyViolation(
                session_id=request.session_id,
                prompt_id=request.prompt_id,
                reason=reason,
                source_refs=request.source_refs,
            )
            violations.append(violation)

        return violations

    async def _check_pattern_violations(self, request: ValidatePromptSafetyRequest) -> list[PromptSafetyViolation]:
        """Check violations against prompt pattern safety rules."""
        violations = []

        # Get all active patterns
        patterns = await self.pattern_repository.list_active()

        for pattern in patterns:
            # Check if prompt violates pattern's safety rules
            for safety_rule in pattern.safety_rules:
                if self._violates_safety_rule(request.prompt_text, safety_rule):
                    violation = PromptSafetyViolation(
                        session_id=request.session_id,
                        prompt_id=request.prompt_id,
                        reason=f"Violates safety rule from pattern '{pattern.name}': {safety_rule}",
                        source_refs=request.source_refs + [pattern.id],
                    )
                    violations.append(violation)

        return violations

    def _violates_safety_rule(self, prompt_text: str, safety_rule: str) -> bool:
        """Check if prompt text violates a specific safety rule.

        Args:
            prompt_text: The prompt text to check
            safety_rule: The safety rule to check against

        Returns:
            True if the prompt violates the rule, False otherwise
        """
        # Simple keyword matching - production would use more sophisticated NLP
        rule_lower = safety_rule.lower()
        prompt_lower = prompt_text.lower()

        # Check if the rule contains forbidden terms
        if "no" in rule_lower or "avoid" in rule_lower or "prohibited" in rule_lower:
            # Extract the forbidden term
            if ":" in safety_rule:
                forbidden_part = safety_rule.split(":", 1)[1].strip().lower()
                if forbidden_part in prompt_lower:
                    return True

        return False
