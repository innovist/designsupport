"""Use case: List generation jobs for a session."""
from typing import Optional

from apps.generation.application.dtos import GenerationJobResponse
from apps.generation.application.ports import GenerationJobRepositoryPort
from apps.generation.domain.value_objects import GenerationStatus, GenerationKind
from shared.application.result import Result


class ListGenerationJobsUseCase:
    """Use case for listing generation jobs."""

    def __init__(self, job_repository: GenerationJobRepositoryPort):
        """Initialize use case.

        Args:
            job_repository: Repository for jobs
        """
        self.job_repository = job_repository

    async def execute(
        self,
        session_id: str,
        status: Optional[GenerationStatus] = None,
        kind: Optional[GenerationKind] = None,
        limit: int = 50
    ) -> Result[list[GenerationJobResponse]]:
        """Execute the use case.

        Args:
            session_id: Session identifier
            status: Optional status filter
            kind: Optional kind filter
            limit: Maximum results to return

        Returns:
            Result containing list of job responses
        """
        from uuid import UUID

        # Convert session_id to UUID
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            return Result.failure(
                ValueError(f"Invalid session_id format: {session_id}")
            )

        # Find jobs
        result = await self.job_repository.find_by_session(
            session_id=session_uuid,
            status=status,
            kind=kind,
            limit=limit
        )

        if result.is_failure:
            return result

        jobs = result.value

        # Convert to responses
        responses = [self._to_response(job) for job in jobs]

        return Result.success(responses)

    def _to_response(self, job) -> GenerationJobResponse:
        """Convert domain entity to response DTO.

        Args:
            job: Generation job entity

        Returns:
            GenerationJobResponse
        """
        return GenerationJobResponse(
            id=job.id,
            session_id=job.session_id,
            kind=job.kind,
            prompt_id=job.prompt_id,
            brief_id=job.brief_id,
            concept_id=job.concept_id,
            rule_ids=job.rule_ids,
            sketch_id=job.sketch_id,
            reference_ids=job.reference_ids,
            status=job.status,
            model_policy_key=job.model_policy_key,
            retries=job.retries,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )
