"""Use case: Get generation result details."""
from uuid import UUID

from apps.generation.application.dtos import GenerationJobResponse, GeneratedDesignResponse
from apps.generation.application.ports import (
    GenerationJobRepositoryPort,
    GeneratedDesignRepositoryPort
)
from shared.application.result import Result
from shared.domain.exceptions import NotFoundError


class GetGenerationResultUseCase:
    """Use case for getting generation result details."""

    def __init__(
        self,
        job_repository: GenerationJobRepositoryPort,
        design_repository: GeneratedDesignRepositoryPort
    ):
        """Initialize use case.

        Args:
            job_repository: Repository for jobs
            design_repository: Repository for generated designs
        """
        self.job_repository = job_repository
        self.design_repository = design_repository

    async def execute(self, job_id: str) -> Result[dict]:
        """Execute the use case.

        Args:
            job_id: Job identifier

        Returns:
            Result containing job and designs dict or error
        """
        # Convert job_id to UUID
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            return Result.failure(
                ValueError(f"Invalid job_id format: {job_id}")
            )

        # Find job
        job_result = await self.job_repository.find_by_id(job_uuid)
        if job_result.is_failure:
            return Result.failure(NotFoundError("GenerationJob", job_id))

        job = job_result.value

        # Find designs for this job
        designs_result = await self.design_repository.find_by_job(job_uuid)
        if designs_result.is_failure:
            return designs_result

        designs = designs_result.value

        # Build response
        return Result.success({
            "job": self._job_to_response(job),
            "designs": [self._design_to_response(d) for d in designs]
        })

    def _job_to_response(self, job) -> GenerationJobResponse:
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

    def _design_to_response(self, design) -> GeneratedDesignResponse:
        """Convert domain entity to response DTO.

        Args:
            design: Generated design entity

        Returns:
            GeneratedDesignResponse
        """
        return GeneratedDesignResponse(
            id=design.id,
            job_id=design.job_id,
            asset_uri=design.asset_uri,
            asset_kind=design.asset_kind,
            parent_sketch_id=design.parent_sketch_id,
            brief_id=design.brief_id,
            concept_id=design.concept_id,
            rule_ids=design.rule_ids,
            reference_ids=design.reference_ids,
            model_policy_key=design.model_policy_key,
            prompt_id=design.prompt_id,
            created_at=design.created_at.isoformat()
        )
