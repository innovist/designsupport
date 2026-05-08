"""Use case: Create a new generation job."""
from uuid import UUID

from apps.generation.application.dtos import CreateGenerationJobRequest, GenerationJobResponse
from apps.generation.application.ports import GenerationJobRepositoryPort
from apps.generation.domain.entities import GenerationJob
from apps.generation.domain.services import GenerationJobValidator
from apps.generation.domain.value_objects import GenerationStatus
from shared.application.result import Result
from shared.domain.exceptions import ValidationError


class CreateGenerationJobUseCase:
    """Use case for creating a new generation job.

    REQ-03-GEN-001: GenerationJob tracks all creation metadata
    REQ-03-GEN-002: Job MUST link to at least one of: brief, concept, rule, reference
    """

    def __init__(
        self,
        job_repository: GenerationJobRepositoryPort,
        validator: GenerationJobValidator
    ):
        """Initialize use case.

        Args:
            job_repository: Repository for persisting jobs
            validator: Job validator
        """
        self.job_repository = job_repository
        self.validator = validator

    async def execute(self, request: CreateGenerationJobRequest) -> Result[GenerationJobResponse]:
        """Execute the use case.

        Args:
            request: Job creation request

        Returns:
            Result containing job response or error
        """
        # Create domain entity
        job = GenerationJob(
            session_id=request.session_id,
            kind=request.kind,
            prompt_id=request.prompt_id,
            brief_id=request.brief_id,
            concept_id=request.concept_id,
            rule_ids=request.rule_ids or [],
            sketch_id=request.sketch_id,
            reference_ids=request.reference_ids or [],
            status=GenerationStatus.QUEUED,
            model_policy_key=request.model_policy_key
        )

        # Validate job
        try:
            self.validator.validate_job_creation(job)
        except ValidationError as e:
            return Result.failure(e)

        # Save job
        save_result = await self.job_repository.save(job)
        if save_result.is_failure:
            return save_result

        saved_job = save_result.value

        # Return response
        return Result.success(self._to_response(saved_job))

    def _to_response(self, job: GenerationJob) -> GenerationJobResponse:
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
