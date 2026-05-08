"""Celery tasks for async model invocation.

Implements REQ-04-ASYNC-001: Async model invocation with Celery.
"""
import asyncio
import uuid
from datetime import datetime, timezone

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from apps.model_catalog.domain.entities import InvocationStatus, ModelInvocation
from apps.model_catalog.domain.services import ModelRouter
from apps.model_catalog.infrastructure.repositories import (
    ModelInvocationRepository,
    FeatureModelPolicyRepository,
    ModelCatalogRepository,
)
from apps.model_catalog.domain.services import CostGuard
from shared.domain.exceptions import OperationError


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,  # 5 minutes
    time_limit=600,  # 10 minutes hard limit
)
def invoke_model_task(
    self,
    feature_key: str,
    payload: dict,
    options: dict,
    tenant_id: str,
    workspace_id: str,
    session_id: str | None = None,
):
    """Async task for model invocation with fallback chain.

    Implements REQ-04-ASYNC-001: Async invocation with retry policy.
    Implements REQ-04-ROUTER-002: Primary first, then fallback chain.

    Args:
        self: Celery task instance
        feature_key: Feature identifier
        payload: Request payload
        options: Model options
        tenant_id: Tenant ID
        workspace_id: Workspace ID
        session_id: Optional session ID

    Returns:
        Dict with invocation result

    Raises:
        Exception: If all retries exhausted
    """
    # Initialize repositories and services
    policy_repo = FeatureModelPolicyRepository()
    model_repo = ModelCatalogRepository()
    invocation_repo = ModelInvocationRepository()
    cost_guard = CostGuard()

    # Initialize model router
    router = ModelRouter(
        policy_repository=policy_repo,
        model_repository=model_repo,
        invocation_repository=invocation_repo,
        cost_guard=cost_guard,
    )

    try:
        # Invoke model (bridge async router from sync Celery task)
        response, invocation = asyncio.run(router.invoke(
            feature_key=feature_key,
            payload=payload,
            options=options,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            session_id=session_id,
        ))

        # Return success result
        return {
            "invocation_id": invocation.id,
            "status": invocation.status.value,
            "model_id": invocation.model_id,
            "response": response,
            "tokens_in": invocation.tokens_in,
            "tokens_out": invocation.tokens_out,
            "cost_estimate": invocation.cost_estimate,
            "latency_ms": invocation.latency_ms,
        }

    except SoftTimeLimitExceeded:
        # Soft timeout - log and mark as timeout
        invocation = ModelInvocation(
            id=f"inv-{uuid.uuid4().hex}",
            feature_key=feature_key,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            session_id=session_id,
            model_id="unknown",
            status=InvocationStatus.TIMEOUT,
            error_code="TIMEOUT",
            error_summary="Task exceeded soft time limit",
            created_at=datetime.now(timezone.utc),
        )

        # Use sync repository method for Celery task
        invocation_repo.create_sync(invocation)

        # Retry with exponential backoff
        try:
            raise self.retry(exc=SoftTimeLimitExceeded("Soft timeout"), countdown=2 ** self.request.retries)
        except Exception:
            # Max retries exhausted
            return {
                "invocation_id": invocation.id,
                "status": "timeout",
                "error": "Task exceeded maximum retry attempts due to timeout",
            }

    except Exception as e:
        # Log failure and retry
        invocation = ModelInvocation(
            id=f"inv-{uuid.uuid4().hex}",
            feature_key=feature_key,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            session_id=session_id,
            model_id="unknown",
            status=InvocationStatus.FAILURE,
            error_code="TASK_FAILED",
            error_summary=str(e),
            created_at=datetime.now(timezone.utc),
        )

        # Use sync repository method for Celery task
        invocation_repo.create_sync(invocation)

        # Retry on transient errors
        if "timeout" in str(e).lower() or "rate limit" in str(e).lower():
            try:
                raise self.retry(exc=e, countdown=2 ** self.request.retries)
            except Exception:
                # Max retries exhausted
                return {
                    "invocation_id": invocation.id,
                    "status": "failure",
                    "error": f"Task failed after {self.max_retries} retries: {str(e)}",
                }

        # Non-retryable error
        return {
            "invocation_id": invocation.id,
            "status": "failure",
            "error": str(e),
        }


@shared_task
def aggregate_metrics_task(
    feature_key: str,
    start_time: str | None = None,
    end_time: str | None = None,
):
    """Async task for aggregating model invocation metrics.

    Args:
        feature_key: Feature to aggregate metrics for
        start_time: Start of time range (ISO format)
        end_time: End of time range (ISO format)

    Returns:
        Aggregated metrics dict
    """
    invocation_repo = ModelInvocationRepository()

    # Parse time range
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None

    # Aggregate metrics
    metrics = invocation_repo.aggregate_metrics(
        feature_key=feature_key,
        start_time=start_dt,
        end_time=end_dt,
    )

    return metrics


@shared_task
def cleanup_old_invocations_task(days_to_keep: int = 30):
    """Async task for cleaning up old invocation records.

    Args:
        days_to_keep: Number of days to retain (default: 30)

    Returns:
        Number of records deleted
    """
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days_to_keep)

    # Delete old invocations
    deleted_count = ModelInvocationRepository().delete_old_records(cutoff_date)

    return {
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
    }
