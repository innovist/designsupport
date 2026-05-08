"""Celery tasks for async generation execution."""
import os
import logging

from celery import shared_task

from apps.generation.application.use_cases.execute_generation_job import ExecuteGenerationJobUseCase
from apps.generation.application.dtos import ExecuteJobRequest
from apps.generation.application.ports import ObjectStoragePort
from shared.domain.exceptions import NotFoundError, OperationError

logger = logging.getLogger(__name__)


# @MX:WARN: [AUTO] Async Celery task with external model dependencies and retry logic
# @MX:REASON: Background task can fail silently; max_retries=3 may delay error detection
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def execute_generation_task(self, job_id: str):
    """Execute a generation job asynchronously.

    This task is triggered by the execute_generation_job use case
    and runs in the background to avoid blocking the API response.

    Args:
        job_id: Generation job identifier

    Returns:
        dict: Execution result with status and design IDs

    Raises:
        Exception: On unrecoverable errors (after max retries)
    """
    from apps.generation.domain.services import FallbackChainExecutor
    from apps.generation.infrastructure.repositories.generation_job_repository import DjangoGenerationJobRepository
    from apps.generation.infrastructure.repositories.generated_design_repository import DjangoGeneratedDesignRepository
    from apps.generation.application.ports import ModelRouterPort
    from apps.generation.domain.entities import CostMetadata
    from apps.model_catalog.domain.services import ModelRouter
    from apps.model_catalog.infrastructure.repositories import (
        DjangoFeatureModelPolicyRepository,
        DjangoModelCatalogRepository,
        DjangoModelInvocationRepository,
    )
    from apps.model_catalog.domain.services import CostGuard
    from shared.application.result import Result
    from shared.domain.exceptions import OperationError
    from uuid import UUID

    logger.info(f"Executing generation job {job_id}")

    try:
        # Initialize SPEC-04 ModelRouter
        # REQ-04-ROUTER-001: Single entry point for model calls
        policy_repo = DjangoFeatureModelPolicyRepository()
        model_repo = DjangoModelCatalogRepository()
        invocation_repo = DjangoModelInvocationRepository()
        cost_guard = CostGuard(policy_repository=policy_repo)

        model_router_domain = ModelRouter(
            policy_repository=policy_repo,
            model_repository=model_repo,
            invocation_repository=invocation_repo,
            cost_guard=cost_guard,
        )

        # Create adapter to bridge ModelRouterPort interface with SPEC-04 ModelRouter
        # @MX:ANCHOR: [AUTO] Adapter bridging ModelRouterPort to SPEC-04 ModelRouter
        # @MX:REASON: Integration point between generation module and model catalog system
        # @MX:SPEC: REQ-03-GEN-006, REQ-04-ROUTER-002
        class ModelRouterAdapter(ModelRouterPort):
            """Adapter for SPEC-04 ModelRouter domain service.

            REQ-03-GEN-006: All model calls go through SPEC-04 ModelRouter
            REQ-04-ROUTER-002: Primary first, then fallback chain
            """

            def __init__(self, domain_router: ModelRouter, tenant_id: str, workspace_id: str):
                """Initialize adapter with domain router and context.

                Args:
                    domain_router: SPEC-04 ModelRouter domain service
                    tenant_id: Tenant identifier for routing
                    workspace_id: Workspace identifier for routing
                """
                self.domain_router = domain_router
                self.tenant_id = tenant_id
                self.workspace_id = workspace_id

            # @MX:WARN: [AUTO] Async model invocation with external API dependencies
            # @MX:REASON: ModelRouter.invoke triggers fallback chain; failure affects entire generation job
            async def generate_image(
                self,
                model_key: str,
                prompt: str,
                policy_key: str,
                size: str = "1024x1024",
                n: int = 1
            ) -> Result:
                """Generate image using SPEC-04 ModelRouter.

                Args:
                    model_key: Model identifier (kept for compatibility, ignored in favor of policy)
                    prompt: Generation prompt
                    policy_key: Feature policy key for routing
                    size: Image size
                    n: Number of images

                Returns:
                    Result with asset_uri and cost_metadata
                """
                try:
                    # Call ModelRouter.invoke with fallback chain
                    # REQ-04-ROUTER-002: Primary first, then fallback chain
                    response, invocation = await self.domain_router.invoke(
                        feature_key=policy_key,
                        payload={
                            "prompt": prompt,
                            "size": size,
                            "n": n,
                        },
                        options={},
                        tenant_id=self.tenant_id,
                        workspace_id=self.workspace_id,
                    )

                    # Extract response data
                    asset_uri = response.get("asset_uri")
                    cost_meta_data = response.get("cost_meta")

                    # Convert to CostMetadata entity
                    cost_metadata = CostMetadata(
                        prompt_tokens=cost_meta_data.prompt_tokens,
                        completion_tokens=cost_meta_data.completion_tokens,
                        total_tokens=cost_meta_data.total_tokens,
                        cost_usd=cost_meta_data.cost_usd,
                        model_key=model_key,
                    )

                    # Return result in expected format
                    class GenerateImageResult:
                        def __init__(self, asset_uri, cost_meta):
                            self.asset_uri = asset_uri
                            self.cost_meta = cost_meta

                    return Result.success(GenerateImageResult(
                        asset_uri=asset_uri,
                        cost_meta=cost_metadata
                    ))

                except Exception as e:
                    return Result.failure(
                        OperationError("ModelRouterAdapter", str(e))
                    )

        # Get tenant/workspace context from job
        # For now, use defaults - in production, extract from job context
        tenant_id = "default_tenant"
        workspace_id = "default_workspace"

        # Create adapted model router
        model_router = ModelRouterAdapter(
            domain_router=model_router_domain,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        # Initialize use case dependencies
        job_repo = DjangoGenerationJobRepository()
        design_repo = DjangoGeneratedDesignRepository()

        # Get object storage port implementation
        object_storage = _get_object_storage_port()
        if object_storage is None:
            raise OperationError(
                "execute_generation_task",
                "Object storage not configured. Please configure ObjectStoragePort implementation."
            )

        # Create fallback executor
        fallback_executor = FallbackChainExecutor(
            model_router_port=model_router,
            max_retries_per_model=1
        )

        # Create use case
        use_case = ExecuteGenerationJobUseCase(
            job_repository=job_repo,
            design_repository=design_repo,
            model_router=model_router,
            object_storage=object_storage,
            fallback_executor=fallback_executor
        )

        # Execute use case
        request = ExecuteJobRequest(job_id=UUID(job_id))
        result = use_case.execute(request)

        # Since execute returns a coroutine in async context, we need to run it
        # In production, this would be handled by an async task runner
        # For now, we'll run it synchronously (not ideal but works for demo)
        import asyncio

        # Check if there's an existing event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If running, create task in background
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result_future = pool.submit(
                        asyncio.run,
                        use_case.execute(request)
                    )
                    result = result_future.result()
            else:
                # No loop, run directly
                result = asyncio.run(use_case.execute(request))
        except RuntimeError:
            # No loop, create new one
            result = asyncio.run(use_case.execute(request))

        if result.is_failure:
            logger.error(f"Generation job {job_id} failed: {result.error}")
            raise result.error

        response = result.value
        logger.info(
            f"Generation job {job_id} completed with status {response.status}"
        )

        return {
            "job_id": str(response.job_id),
            "status": response.status.value,
            "design_ids": [str(did) for did in response.design_ids],
            "asset_uris": response.asset_uris,
            "error_message": response.error_message
        }

    except Exception as e:
        logger.error(f"Error executing generation job {job_id}: {str(e)}")
        raise


@shared_task
def cleanup_failed_jobs():
    """Clean up old failed generation jobs.

    This task should be scheduled to run periodically (e.g., daily).
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.generation.infrastructure.orm.models import GenerationJobModel

    # Delete failed jobs older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)

    deleted_count, _ = GenerationJobModel.objects.filter(
        status="failed",
        updated_at__lt=cutoff_date
    ).delete()

    logger.info(f"Cleaned up {deleted_count} old failed generation jobs")

    return {"deleted_count": deleted_count}


def _get_object_storage_port() -> ObjectStoragePort | None:
    """Factory function to get the configured ObjectStoragePort implementation.

    Returns:
        ObjectStoragePort instance or None if not configured

    # @MX:NOTE: [AUTO] Factory function for dependency injection
    # @MX:REASON: Enables proper port configuration without hardcoding implementation
    """
    try:
        # Try to import from shared infrastructure
        from shared.infrastructure.object_storage import S3ObjectStorage
        return S3ObjectStorage()
    except ImportError:
        logger.warning("S3ObjectStorage not available in shared.infrastructure.object_storage")
    try:
        # Try alternative import path
        from apps.generation.infrastructure.object_storage import DjangoObjectStorage
        return DjangoObjectStorage()
    except ImportError:
        logger.warning("DjangoObjectStorage not available in apps.generation.infrastructure.object_storage")

    # No storage implementation available
    return None
