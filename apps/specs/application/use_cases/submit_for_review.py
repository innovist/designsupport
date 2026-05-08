"""Use case: Submit spec document for review."""
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.specs.application.dtos import SpecDocumentDTO, SubmitForReviewRequest
from apps.specs.application.ports import SpecDocumentRepositoryPort
from apps.specs.domain.entities import SpecStatus
from apps.specs.domain.services import SpecDocumentValidator


class SubmitForReviewUseCase:
    """Use case for submitting a spec document for review."""

    def __init__(
        self,
        spec_repository: SpecDocumentRepositoryPort,
        validator: SpecDocumentValidator,
    ):
        self.spec_repository = spec_repository
        self.validator = validator

    async def execute(self, request: SubmitForReviewRequest) -> Result[SpecDocumentDTO]:
        """Execute the use case.

        Args:
            request: SubmitForReviewRequest with spec_id and submitter_id

        Returns:
            Result with SpecDocumentDTO on success, error on failure
        """
        try:
            # Get spec document
            spec = await self.spec_repository.get_by_id(request.spec_id)
            if not spec:
                return Result.failure(NotFoundError("SpecDocument", str(request.spec_id)))

            # Validate current status is draft
            if spec.status != SpecStatus.DRAFT:
                return Result.failure(
                    ValidationError(
                        "status",
                        f"Cannot submit spec with status {spec.status.value}. Must be draft."
                    )
                )

            # Validate spec is ready for review (pre-validation)
            self._validate_for_review(spec)

            # Transition to in_review
            spec.transition_to(SpecStatus.IN_REVIEW)

            # Save spec
            saved_spec = await self.spec_repository.save(spec)

            return Result.success(SpecDocumentDTO.from_entity(saved_spec))

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(ValidationError("spec", f"Failed to submit for review: {str(e)}"))

    def _validate_for_review(self, spec) -> None:
        """Validate that spec is ready for review.

        This is a lighter validation than approval - just check basics.

        Args:
            spec: Spec document to validate

        Raises:
            ValidationError: If validation fails
        """
        # Check all required sections exist
        if not spec.has_all_required_sections():
            missing = self._get_missing_sections(spec)
            raise ValidationError(
                "sections",
                f"Cannot submit for review: missing required sections: {', '.join(missing)}"
            )

        # Check at least some sections have content
        completed_sections = [s for s in spec.sections if s.completed]
        if len(completed_sections) == 0:
            raise ValidationError(
                "sections",
                "Cannot submit for review: no sections have been completed"
            )

    def _get_missing_sections(self, spec) -> list[str]:
        """Get list of missing required section types.

        Args:
            spec: Spec document

        Returns:
            List of missing section type names
        """
        from apps.specs.domain.entities import REQUIRED_SECTION_TYPES

        existing_types = {s.section_type for s in spec.sections}
        required_types = set(REQUIRED_SECTION_TYPES)
        return list(required_types - existing_types)
