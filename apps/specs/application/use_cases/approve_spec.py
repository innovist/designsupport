"""Use case: Approve a spec document."""
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.specs.application.dtos import SpecDocumentDTO, ApproveSpecRequest
from apps.specs.application.ports import SpecDocumentRepositoryPort
from apps.specs.domain.entities import SpecStatus
from apps.specs.domain.services import SpecDocumentValidator, SpecVersionManager


class ApproveSpecUseCase:
    """Use case for approving a spec document.

    Handles version superseding per REQ-03-SPEC-004.
    """

    def __init__(
        self,
        spec_repository: SpecDocumentRepositoryPort,
        validator: SpecDocumentValidator,
        version_manager: SpecVersionManager,
    ):
        self.spec_repository = spec_repository
        self.validator = validator
        self.version_manager = version_manager

    async def execute(self, request: ApproveSpecRequest) -> Result[SpecDocumentDTO]:
        """Execute the use case.

        Args:
            request: ApproveSpecRequest with spec_id, approver_id, and optional change_summary

        Returns:
            Result with SpecDocumentDTO on success, error on failure
        """
        try:
            # Get spec document
            spec = await self.spec_repository.get_by_id(request.spec_id)
            if not spec:
                return Result.failure(NotFoundError("SpecDocument", str(request.spec_id)))

            # Validate for approval (full validation)
            self.validator.validate_for_approval(spec)

            # Handle version superseding if this is a new version
            if spec.supersedes_id:
                await self._handle_version_superseding(spec, request.change_summary)

            # Mark as approved
            spec.mark_approved(request.approver_id)

            # Save spec
            saved_spec = await self.spec_repository.save(spec)

            return Result.success(SpecDocumentDTO.from_entity(saved_spec))

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(ValidationError("spec", f"Failed to approve spec: {str(e)}"))

    async def _handle_version_superseding(self, new_spec, change_summary: str) -> None:
        """Handle superseding of previous version.

        Enforces REQ-03-SPEC-004: Previous version becomes superseded with diff metadata.

        Args:
            new_spec: New version being approved
            change_summary: Summary of changes from old to new version

        Raises:
            ValidationError: If change_summary not provided or old spec not found
        """
        if not change_summary:
            raise ValidationError(
                "change_summary",
                "change_summary is required when approving a new version that supersedes a previous one"
            )

        # Get previous version
        old_spec = await self.spec_repository.get_by_id(new_spec.supersedes_id)
        if not old_spec:
            raise ValidationError(NotFoundError("SpecDocument", str(new_spec.supersedes_id)))

        # Create version diff and supersede
        self.version_manager.handle_new_version_approval(old_spec, new_spec, change_summary)

        # Save old spec with superseded status
        await self.spec_repository.save(old_spec)
