"""Use case: Log prompt safety violations.

REQ-03-PROMPT-006: Record safety violations for auditing.
"""
from uuid import UUID

from shared.application.result import Result

from apps.prompt_library.application.ports import PromptSafetyViolationRepositoryPort
from apps.prompt_library.domain import PromptSafetyViolation


class LogViolationUseCase:
    """Log a prompt safety violation.

    This use case records safety violations for audit trails and
    compliance monitoring.
    """

    def __init__(
        self,
        violation_repository: PromptSafetyViolationRepositoryPort,
    ):
        self.violation_repository = violation_repository

    async def execute(
        self,
        session_id: UUID,
        prompt_id: UUID | None,
        reason: str,
        source_refs: list[UUID],
    ) -> Result[PromptSafetyViolation]:
        """Execute the use case.

        Args:
            session_id: Design session identifier
            prompt_id: Optional prompt identifier
            reason: Reason for the violation
            source_refs: Source references for context

        Returns:
            Result with saved PromptSafetyViolation entity
        """
        violation = PromptSafetyViolation(
            session_id=session_id,
            prompt_id=prompt_id,
            reason=reason,
            source_refs=source_refs,
        )

        saved = await self.violation_repository.save(violation)

        return Result.success(saved)
