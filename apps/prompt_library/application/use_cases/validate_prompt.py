"""Use case: Validate prompt against safety rules.

REQ-03-PROMPT-003: Validate prompts against safety rules.
"""
from typing import Optional
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import ValidationError

from apps.prompt_library.application.ports import (
    PromptPatternRepositoryPort,
    PromptSafetyViolationRepositoryPort,
)
from apps.prompt_library.domain import PromptSafetyViolation


class ValidatePromptUseCase:
    """Validate a prompt against safety rules from active patterns.

    This use case checks prompt text against safety rules defined in
    active prompt patterns and records any violations.
    """

    def __init__(
        self,
        pattern_repository: PromptPatternRepositoryPort,
        violation_repository: PromptSafetyViolationRepositoryPort,
    ):
        self.pattern_repository = pattern_repository
        self.violation_repository = violation_repository

    async def execute(
        self,
        session_id: UUID,
        prompt_id: Optional[UUID],
        prompt_text: str,
        source_refs: list[UUID],
    ) -> Result[dict]:
        """Execute the use case.

        Args:
            session_id: Design session identifier
            prompt_id: Optional prompt identifier
            prompt_text: The prompt text to validate
            source_refs: Source references for context

        Returns:
            Result with dict containing:
                - is_safe (bool): Whether prompt is safe
                - violations (list): List of PromptSafetyViolation entities
        """
        if not prompt_text or not prompt_text.strip():
            return Result.failure(
                ValidationError("prompt_text", "Prompt text cannot be empty")
            )

        violations: list[PromptSafetyViolation] = []

        # Get all active patterns
        patterns = await self.pattern_repository.list_active()

        # Check against each pattern's safety rules
        for pattern in patterns:
            for safety_rule in pattern.safety_rules:
                if self._violates_safety_rule(prompt_text, safety_rule):
                    violation = PromptSafetyViolation(
                        session_id=session_id,
                        prompt_id=prompt_id,
                        reason=f"Violates safety rule from pattern '{pattern.name}': {safety_rule}",
                        source_refs=source_refs + [pattern.id],
                    )
                    violations.append(violation)

        # Save all violations
        saved_violations = []
        for violation in violations:
            saved = await self.violation_repository.save(violation)
            saved_violations.append(saved)

        is_safe = len(saved_violations) == 0

        return Result.success({
            'is_safe': is_safe,
            'violations': saved_violations,
        })

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
        if "no " in rule_lower or "avoid " in rule_lower or "prohibited" in rule_lower:
            # Extract the forbidden term
            if ":" in safety_rule:
                forbidden_part = safety_rule.split(":", 1)[1].strip().lower()
                if forbidden_part in prompt_lower:
                    return True

        return False
