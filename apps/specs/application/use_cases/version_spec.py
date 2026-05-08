"""Use case: Create a new version of a spec document."""
import logging
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.specs.application.dtos import SpecDocumentDTO, VersionSpecRequest
from apps.specs.application.ports import SpecRepositoryPort
from apps.specs.domain.entities import SpecDocument
from apps.specs.domain.value_objects import SpecStatus, VersionDiff

logger = logging.getLogger(__name__)


class VersionSpecUseCase:
    """Use case for creating a new version of a spec document.

    REQ-03-SPEC-005: Preserve discarded/held concepts with reasons
    REQ-03-SPEC-006: Version control with superseding
    """

    def __init__(
        self,
        spec_repository: SpecRepositoryPort,
    ):
        self.spec_repository = spec_repository

    async def execute(self, request: VersionSpecRequest) -> Result[SpecDocumentDTO]:
        """Execute the use case.

        Args:
            request: VersionSpecRequest with spec_id and version_diff

        Returns:
            Result with new SpecDocumentDTO on success, error on failure
        """
        try:
            # Fetch existing spec
            existing_spec = await self.spec_repository.find_by_id(request.spec_id)
            if not existing_spec:
                return Result.failure(
                    NotFoundError("SpecDocument", str(request.spec_id))
                )

            # Validate existing spec can be versioned
            if existing_spec.status != SpecStatus.APPROVED:
                raise ValidationError(
                    "status",
                    f"Only approved specs can be versioned (current: {existing_spec.status.value})"
                )

            # Validate version_diff if provided
            version_diff = request.version_diff
            if version_diff:
                self._validate_version_diff(version_diff)

            # Create new version
            new_version = existing_spec.create_new_version()

            # Copy sections from existing spec
            for section in existing_spec.sections:
                new_version.add_section(section)

            # Copy evidence links
            for link in existing_spec.evidence_links:
                new_version.add_evidence_link(link)

            # Save new version
            saved_new_version = await self.spec_repository.save(new_version)

            # Mark old version as superseded
            existing_spec.supersede_with(saved_new_version, version_diff or VersionDiff(
                changes=["New version created"],
                changed_by=str(request.created_by),
                change_summary="Created new version",
            ))
            await self.spec_repository.save(existing_spec)

            logger.info(
                f"Created new version {saved_new_version.version} of spec {saved_new_version.id}, "
                f"superseding version {existing_spec.version}"
            )

            return Result.success(SpecDocumentDTO.from_entity(saved_new_version))

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            logger.exception(f"Unexpected error in version_spec: {e}")
            return Result.failure(
                ValidationError("spec", f"Failed to version spec: {str(e)}")
            )

    def _validate_version_diff(self, version_diff: VersionDiff) -> None:
        """Validate version diff metadata.

        Args:
            version_diff: VersionDiff to validate

        Raises:
            ValidationError: If validation fails
        """
        if not version_diff.changes or not isinstance(version_diff.changes, list):
            raise ValidationError("changes", "Changes must be a non-empty list")

        if not version_diff.changed_by or not version_diff.changed_by.strip():
            raise ValidationError("changed_by", "Changed by cannot be empty")

        if not version_diff.change_summary or not version_diff.change_summary.strip():
            raise ValidationError("change_summary", "Change summary cannot be empty")
