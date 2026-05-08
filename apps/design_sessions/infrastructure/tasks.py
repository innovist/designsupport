"""Celery tasks for async design session execution.

Implements SPEC-01 §5.3: Async step execution with Celery background tasks.
"""
import logging
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from shared.domain.exceptions import NotFoundError, OperationError

logger = logging.getLogger(__name__)


# @MX:WARN: [AUTO] Async Celery task with soft timeout - failure triggers session FAILED state
# @MX:REASON: Celery task with side effects on session state, requires timeout handling
@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    soft_time_limit=300,  # 5 minutes per step
    time_limit=600,  # 10 minutes hard limit
)
def execute_session_step_task(self, session_id: str, step: int):
    """Execute a design session step asynchronously.

    This task is triggered by the SessionOrchestrator for auto-mode sessions
    and runs in the background to avoid blocking the API response.

    Args:
        session_id: Design session UUID as string
        step: Step number to execute

    Returns:
        dict: Execution result with status and next_step

    Raises:
        Exception: On unrecoverable errors (after max retries)
    """
    from apps.design_sessions.infrastructure.repositories.session_repository import (
        DjangoSessionRepository,
    )
    from apps.design_sessions.application.orchestrator.state_machine import (
        SessionOrchestrator,
        SessionState,
    )
    from apps.design_sessions.infrastructure.repositories.brief_repository import (
        DjangoBriefRepository,
    )
    from apps.design_sessions.infrastructure.repositories.decision_log_repository import (
        DjangoDecisionLogRepository,
    )
    from apps.design_sessions.application.ports import ConversationPort, AssetPort

    logger.info(f"Executing step {step} for session {session_id}")

    try:
        # Initialize repositories and ports
        session_repo = DjangoSessionRepository()
        brief_repo = DjangoBriefRepository()
        decision_repo = DjangoDecisionLogRepository()
        conversation_port: ConversationPort | None = None
        asset_port: AssetPort | None = None

        # Initialize orchestrator
        orchestrator = SessionOrchestrator(
            session_repository=session_repo,
            brief_repository=brief_repo,
            decision_repository=decision_repo,
            conversation_port=conversation_port,
            asset_port=asset_port,
        )

        # Execute the step logic based on current state
        session = session_repo.get_by_id(UUID(session_id))

        if session is None:
            raise NotFoundError(
                "execute_session_step_task",
                f"Session {session_id} not found"
            )

        # Map step to state and execute step-specific logic
        # This is a simplified implementation - full implementation would
        # call actual step handlers (research, concept, reference, etc.)
        current_state = SessionState(session.status.value)

        # Execute step-specific business logic
        # In production, this would dispatch to step-specific handlers
        logger.info(f"Executing {current_state.value} step for session {session_id}")

        # For now, just transition to next state (placeholder for actual step logic)
        next_state = orchestrator._get_next_state(current_state)

        if next_state:
            # Auto-transition to next state
            session = orchestrator.transition_session(
                session_id=UUID(session_id),
                new_state=next_state,
                actor='auto',
                rationale=f'Auto-completed step {step}',
            )

            logger.info(
                f"Step {step} completed for session {session_id}, "
                f"transitioned to {next_state.value}"
            )

            return {
                "session_id": session_id,
                "step": step,
                "status": "completed",
                "next_state": session.status.value,
                "next_step": session.current_step.value,            }
        else:
            # Terminal state reached
            logger.info(f"Session {session_id} reached terminal state")
            return {
                "session_id": session_id,
                "step": step,
                "status": "completed",
                "next_state": session.status.value,
                "next_step": None,
            }

    except SoftTimeLimitExceeded:
        # Handle soft timeout - transition to failed state
        # @MX:WARN: [AUTO] Timeout triggers session state mutation to FAILED
        # @MX:REASON: Side effect on domain state, requires careful error handling
        logger.error(f"Step {step} for session {session_id} timed out after 5 minutes")

        # Mark session as failed
        _mark_session_failed(UUID(session_id), step, "Step execution timed out")

        raise OperationError(
            "execute_session_step_task",
            f"Step {step} execution timed out for session {session_id}"
        )

    except Exception as e:
        logger.error(f"Error executing step {step} for session {session_id}: {str(e)}")

        # Mark session as failed
        _mark_session_failed(UUID(session_id), step, str(e))

        raise


def _mark_session_failed(session_id: UUID, step: int, error_message: str):
    """Mark a session as failed after step execution error.

    Args:
        session_id: Session UUID
        step: Step number that failed
        error_message: Error description
    """
    from apps.design_sessions.infrastructure.repositories.session_repository import (
        DjangoSessionRepository,
    )
    from apps.design_sessions.application.orchestrator.state_machine import (
        SessionOrchestrator,
        SessionState,
    )
    from apps.design_sessions.infrastructure.repositories.brief_repository import (
        DjangoBriefRepository,
    )
    from apps.design_sessions.infrastructure.repositories.decision_log_repository import (
        DjangoDecisionLogRepository,
    )
    from apps.design_sessions.application.ports import ConversationPort, AssetPort

    try:
        # Initialize orchestrator
        session_repo = DjangoSessionRepository()
        brief_repo = DjangoBriefRepository()
        decision_repo = DjangoDecisionLogRepository()
        conversation_port: ConversationPort | None = None
        asset_port: AssetPort | None = None

        orchestrator = SessionOrchestrator(
            session_repository=session_repo,
            brief_repository=brief_repo,
            decision_repository=decision_repo,
            conversation_port=conversation_port,
            asset_port=asset_port,
        )

        # Transition to failed state
        orchestrator.handle_step_failure(
            session_id=session_id,
            error_message=error_message,
            step=step,
        )

        logger.info(f"Session {session_id} marked as failed due to error in step {step}")

    except Exception as e:
        logger.error(
            f"Failed to mark session {session_id} as failed: {str(e)}"
        )


# @MX:WARN: [AUTO] Scheduled task mutates session state - requires idempotency
# @MX:REASON: Bulk state mutation on stale sessions, potential data loss if misconfigured
@shared_task
def cleanup_stale_sessions():
    """Clean up stale design sessions.

    This task should be scheduled to run periodically (e.g., daily).
    Removes sessions stuck in intermediate states for too long.

    Returns:
        dict: Cleanup statistics
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.design_sessions.infrastructure.orm.models import DesignSessionModel

    # Mark sessions as failed if stuck in non-terminal state for > 24 hours
    cutoff_date = timezone.now() - timedelta(hours=24)

    stale_count = DesignSessionModel.objects.filter(
        updated_at__lt=cutoff_date,
        status__in=[
            'queued',
            'researching',
            'concepting',
            'referencing',
            'abstracting',
            'generating',
            'documenting',
        ]
    ).update(status='failed')

    logger.info(f"Marked {stale_count} stale sessions as failed")

    return {"stale_count": stale_count}
