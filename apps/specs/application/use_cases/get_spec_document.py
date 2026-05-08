"""Use case: Get a spec document."""
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError

from apps.specs.application.dtos import SpecDocumentDTO
from apps.specs.application.ports import SpecDocumentRepositoryPort


class GetSpecDocumentUseCase:
    """Use case for retrieving a spec document."""

    def __init__(self, spec_repository: SpecDocumentRepositoryPort):
        self.spec_repository = spec_repository

    async def execute(self, spec_id: UUID) -> Result[SpecDocumentDTO]:
        """Execute the use case.

        Args:
            spec_id: Spec UUID

        Returns:
            Result with SpecDocumentDTO on success, error on failure
        """
        try:
            # Get spec document
            spec = await self.spec_repository.get_by_id(spec_id)
            if not spec:
                return Result.failure(NotFoundError("SpecDocument", str(spec_id)))

            return Result.success(SpecDocumentDTO.from_entity(spec))

        except Exception as e:
            return Result.failure(e)
