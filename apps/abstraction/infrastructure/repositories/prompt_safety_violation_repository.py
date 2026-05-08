"""Repository implementation for PromptSafetyViolation entities."""
from uuid import UUID

from apps.abstraction.application.ports import PromptSafetyViolationRepositoryPort
from apps.abstraction.domain.entities import PromptSafetyViolation
from apps.abstraction.infrastructure.orm.models import PromptSafetyViolationModel


class DjangoPromptSafetyViolationRepository(PromptSafetyViolationRepositoryPort):
    """Django ORM implementation of PromptSafetyViolation repository."""

    async def save(self, violation: PromptSafetyViolation) -> PromptSafetyViolation:
        """Save a safety violation."""
        orm_violation = PromptSafetyViolationModel.from_domain(violation)
        orm_violation.save()
        return orm_violation.to_domain()

    async def list_by_session(self, session_id: UUID) -> list[PromptSafetyViolation]:
        """List all violations for a session."""
        orm_violations = PromptSafetyViolationModel.objects.filter(
            session_id=str(session_id)
        ).order_by('-created_at')

        return [violation.to_domain() for violation in orm_violations]
