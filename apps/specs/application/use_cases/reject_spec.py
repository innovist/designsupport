"""Use case: Reject a spec document."""
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.specs.application.dtos import RejectSpecRequest, SpecDocumentDTO
from apps.specs.application.ports import SpecDocumentRepositoryPort
from apps.specs.domain.entities import SpecStatus
from apps.specs.domain.value_objects import SpecSection


class RejectSpecUseCase:
    """Use case for rejecting a spec document."""

    def __init__(self, spec_repository: SpecDocumentRepositoryPort):
        self.spec_repository = spec_repository

    async def execute(self, request: RejectSpecRequest) -> Result[SpecDocumentDTO]:
        """Execute the use case.

        Args:
            request: RejectSpecRequest with spec_id, reviewer_id, and rejection_reason

        Returns:
            Result with SpecDocumentDTO on success, error on failure
        """
        try:
            # Get spec document
            spec = await self.spec_repository.get_by_id(request.spec_id)
            if not spec:
                return Result.failure(NotFoundError("SpecDocument", str(request.spec_id)))

            # Validate current status
            if spec.status != SpecStatus.IN_REVIEW:
                return Result.failure(
                    ValidationError(
                        "status",
                        f"Cannot reject spec with status {spec.status.value}. Must be in_review."
                    )
                )

            # Validate rejection reason
            if not request.rejection_reason or not request.rejection_reason.strip():
                return Result.failure(ValidationError("rejection_reason", "Rejection reason cannot be empty"))

            # Add rejection reason to a feedback section
            self._add_rejection_feedback(spec, request.rejection_reason, request.reviewer_id)

            # Transition to rejected
            spec.transition_to(SpecStatus.REJECTED)

            # Save spec
            saved_spec = await self.spec_repository.save(spec)

            return Result.success(SpecDocumentDTO.from_entity(saved_spec))

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(ValidationError("spec", f"Failed to reject spec: {str(e)}"))

    def _add_rejection_feedback(self, spec, reason: str, reviewer_id: UUID) -> None:
        """Add rejection feedback to spec document.

        Args:
            spec: Spec document to add feedback to
            reason: Rejection reason
            reviewer_id: ID of reviewer who rejected
        """
        # Create or update a feedback section
        feedback_section = spec.get_section("rejection_feedback")

        feedback_data = {
            "reason": reason,
            "reviewer_id": str(reviewer_id),
            "rejected_at": spec.updated_at.isoformat(),
        }

        if feedback_section:
            # Update existing feedback section
            feedback_section.content = feedback_data
            feedback_section.completed = True
        else:
            # Create new feedback section
            new_section = SpecSection(
                section_type="rejection_feedback",
                title="Rejection Feedback",
                content=feedback_data,
                evidence_links=[],
                required=False,  # Feedback section is not required
                completed=True,
            )
            spec.add_section(new_section)
