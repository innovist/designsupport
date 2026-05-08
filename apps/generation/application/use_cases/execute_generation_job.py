"""Use case: Execute a generation job."""
from uuid import UUID

from apps.generation.application.dtos import ExecuteJobRequest, ExecuteJobResponse
from apps.generation.application.ports import (
    GenerationJobRepositoryPort,
    GeneratedDesignRepositoryPort,
    ModelRouterPort,
    ObjectStoragePort
)
from apps.generation.domain.entities import GeneratedDesign
from apps.generation.domain.services import FallbackChainExecutor
from apps.generation.domain.value_objects import (
    GenerationStatus,
    AssetKind
)
from shared.application.result import Result
from shared.domain.exceptions import (
    NotFoundError,
    OperationError,
    StateTransitionError
)


class ExecuteGenerationJobUseCase:
    """Use case for executing a generation job.

    REQ-03-GEN-006: All model calls go through SPEC-04 ModelRouter
    REQ-03-GEN-007: On failure → NO fake/placeholder images, record failure
    REQ-03-GEN-008: Primary image provider = ByteDance Seedream 4.5
    REQ-03-GEN-010: Fallback chain for model providers
    """

    def __init__(
        self,
        job_repository: GenerationJobRepositoryPort,
        design_repository: GeneratedDesignRepositoryPort,
        model_router: ModelRouterPort,
        object_storage: ObjectStoragePort,
        fallback_executor: FallbackChainExecutor
    ):
        """Initialize use case.

        Args:
            job_repository: Repository for jobs
            design_repository: Repository for generated designs
            model_router: Model router for image generation
            object_storage: Object storage for assets
            fallback_executor: Fallback chain executor
        """
        self.job_repository = job_repository
        self.design_repository = design_repository
        self.model_router = model_router
        self.object_storage = object_storage
        self.fallback_executor = fallback_executor

    async def execute(self, request: ExecuteJobRequest) -> Result[ExecuteJobResponse]:
        """Execute the use case.

        Args:
            request: Job execution request

        Returns:
            Result containing execution response or error
        """
        # Find job
        job_result = await self.job_repository.find_by_id(request.job_id)
        if job_result.is_failure:
            return Result.failure(NotFoundError("GenerationJob", str(request.job_id)))

        job = job_result.value

        # Check if job can be executed
        if job.status != GenerationStatus.QUEUED and not request.force_retry:
            return Result.failure(
                StateTransitionError(
                    job.status.value,
                    GenerationStatus.RUNNING.value
                )
            )

        # Transition to running
        job.transition_to(GenerationStatus.RUNNING)
        await self.job_repository.save(job)

        # Execute generation
        try:
            execution_result = await self._execute_generation(job)

            if execution_result["success"]:
                # Save generated designs
                design_ids = []
                asset_uris = []

                for asset_data in execution_result["assets"]:
                    design = GeneratedDesign(
                        job_id=job.id,
                        asset_uri=asset_data["uri"],
                        asset_kind=AssetKind.IMAGE,
                        parent_sketch_id=job.sketch_id,
                        brief_id=job.brief_id,
                        concept_id=job.concept_id,
                        rule_ids=job.rule_ids,
                        reference_ids=job.reference_ids,
                        model_policy_key=execution_result["model_key"],
                        prompt_id=job.prompt_id
                    )

                    save_result = await self.design_repository.save(design)
                    if save_result.is_failure:
                        return save_result

                    design_ids.append(design.id)
                    asset_uris.append(design.asset_uri)

                # Update job to completed
                job.transition_to(GenerationStatus.COMPLETED)
                if execution_result.get("cost_meta"):
                    from apps.generation.domain.entities import CostMetadata
                    job.update_cost(execution_result["cost_meta"])

                await self.job_repository.save(job)

                return Result.success(ExecuteJobResponse(
                    job_id=job.id,
                    status=job.status,
                    design_ids=design_ids,
                    asset_uris=asset_uris,
                    cost_metadata=execution_result.get("cost_meta").__dict__ if execution_result.get("cost_meta") else None,
                    error_message=None
                ))

            else:
                # Generation failed
                error_msg = execution_result.get("error", "Unknown error")
                job.transition_to(GenerationStatus.FAILED, error=error_msg)
                await self.job_repository.save(job)

                return Result.success(ExecuteJobResponse(
                    job_id=job.id,
                    status=job.status,
                    design_ids=[],
                    asset_uris=[],
                    cost_metadata=None,
                    error_message=error_msg
                ))

        except Exception as e:
            # Unexpected error
            job.transition_to(GenerationStatus.FAILED, error=str(e))
            await self.job_repository.save(job)

            return Result.failure(OperationError("execute_generation", str(e)))

    async def _execute_generation(self, job) -> dict:
        """Execute the actual generation with fallback chain.

        REQ-03-GEN-007: NO fake/placeholder images on failure
        REQ-03-GEN-010: Use fallback chain

        Args:
            job: Generation job

        Returns:
            Dict with success status, assets, model_key, cost_meta, error
        """
        # Build prompt from job context
        prompt = await self._build_prompt(job)

        # Execute with fallback chain
        try:
            model_result = await self.fallback_executor.execute_with_fallback(
                prompt=prompt,
                model_policy_key=job.model_policy_key
            )

            # Upload generated image to object storage
            # Note: In real implementation, model_result.asset_uri would be downloaded
            # and then uploaded to object storage. For now, we assume the model
            # returns a URL that we can use directly.

            return {
                "success": True,
                "assets": [{"uri": model_result.asset_uri}],
                "model_key": model_result.model_key,
                "cost_meta": model_result.cost_meta
            }

        except OperationError as e:
            # All models in fallback chain failed
            return {
                "success": False,
                "assets": [],
                "error": str(e)
            }

    async def _build_prompt(self, job) -> str:
        """Build generation prompt from job context.

        Args:
            job: Generation job

        Returns:
            Prompt string
        """
        # This is a simplified prompt builder
        # In real implementation, this would fetch context from
        # brief, concept, rules, and references to build a rich prompt

        prompt_parts = []

        if job.brief_id:
            prompt_parts.append(f"Design brief: {job.brief_id}")

        if job.concept_id:
            prompt_parts.append(f"Concept: {job.concept_id}")

        if job.rule_ids:
            prompt_parts.append(f"Apply rules: {', '.join(map(str, job.rule_ids))}")

        if job.reference_ids:
            prompt_parts.append(f"References: {', '.join(map(str, job.reference_ids))}")

        # Add kind-specific instructions
        if job.kind == GenerationKind.SKETCH:
            prompt_parts.append("Create initial design sketch")
        elif job.kind == GenerationKind.REFINEMENT:
            prompt_parts.append("Refine existing design with new variations")
        elif job.kind == GenerationKind.VARIATION:
            prompt_parts.append("Create design variations applying abstraction rules")
        elif job.kind == GenerationKind.DOMAIN_APPLICATION:
            prompt_parts.append("Apply design to specific domain format")

        return " | ".join(prompt_parts)
