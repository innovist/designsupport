"""Use case: List concept candidates for a session."""
from uuid import UUID

from shared.application.result import Result

from apps.concepts.application.dtos import ConceptCandidateDTO
from apps.concepts.application.ports import ConceptRepositoryPort


class ListConceptsBySessionUseCase:
    """Use case for listing concepts by session."""

    def __init__(self, concept_repository: ConceptRepositoryPort):
        self.concept_repository = concept_repository

    async def execute(self, session_id: UUID) -> Result[list[ConceptCandidateDTO]]:
        """Execute the use case.

        Args:
            session_id: Session UUID

        Returns:
            Result with list of ConceptCandidateDTO
        """
        try:
            concepts = await self.concept_repository.list_by_session(session_id)
            dtos = [ConceptCandidateDTO.from_entity(c) for c in concepts]
            return Result.success(dtos)
        except Exception as e:
            return Result.failure(
                ValidationError("session", f"Failed to list concepts: {str(e)}")
            )
