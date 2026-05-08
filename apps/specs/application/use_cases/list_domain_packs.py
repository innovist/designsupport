"""Use case: List domain packs."""
from shared.application.result import Result

from apps.specs.application.dtos import DomainPackDTO
from apps.specs.application.ports import DomainPackRepositoryPort


class ListDomainPacksUseCase:
    """Use case for listing all available domain packs."""

    def __init__(self, domain_pack_repository: DomainPackRepositoryPort):
        self.domain_pack_repository = domain_pack_repository

    async def execute(self) -> Result[list[DomainPackDTO]]:
        """Execute the use case.

        Returns:
            Result with list of DomainPackDTO on success, error on failure
        """
        try:
            # Get all domain packs
            packs = await self.domain_pack_repository.list_all()

            # Convert to DTOs
            pack_dtos = [DomainPackDTO.from_entity(pack) for pack in packs]

            return Result.success(pack_dtos)

        except Exception as e:
            return Result.failure(e)
