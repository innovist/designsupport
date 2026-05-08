"""Session orchestrator state machine.

Manages design session lifecycle with state transitions,
step execution, and decision tracking.
"""
import logging
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from apps.design_sessions.application.ports import (
    AssetPort,
    BriefRepositoryPort,
    ConversationPort,
    DecisionLogRepositoryPort,
    SessionRepositoryPort,
)
from apps.design_sessions.domain.entities import (
    DecisionLog,
    DesignBrief,
    DesignSession,
)
from apps.design_sessions.domain.value_objects import SessionMode, SessionStatus, PipelineStep
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Design session states following SPEC-01 §5.3."""

    QUEUED = 'queued'
    RESEARCHING = 'researching'
    CONCEPTING = 'concepting'
    REFERENCING = 'referencing'
    ABSTRACTING = 'abstracting'
    GENERATING = 'generating'
    DOCUMENTING = 'documenting'
    REVIEW_READY = 'review_ready'
    FAILED = 'failed'


class ExecutionMode(str, Enum):
    """Session execution modes."""

    AUTO = 'auto'
    GUIDED = 'guided'


class SessionOrchestrator:
    """Orchestrates design session lifecycle through state machine.

    Manages:
    - State transitions following SPEC-01 §5.3
    - Auto vs guided mode behavior
    - Step execution with Celery async tasks
    - Decision recording (user and auto)
    - Failure recovery
    - Re-run with versioning
    """

    # Valid state transitions per SPEC-01 §5.3
    _VALID_TRANSITIONS: Dict[SessionState, List[SessionState]] = {
        SessionState.QUEUED: [
            SessionState.RESEARCHING,
            SessionState.CONCEPTING,
            SessionState.REFERENCING,
            SessionState.ABSTRACTING,
            SessionState.GENERATING,
            SessionState.DOCUMENTING,
            SessionState.REVIEW_READY,
            SessionState.FAILED,
        ],
        SessionState.RESEARCHING: [
            SessionState.CONCEPTING,
            SessionState.FAILED,
        ],
        SessionState.CONCEPTING: [
            SessionState.REFERENCING,
            SessionState.FAILED,
        ],
        SessionState.REFERENCING: [
            SessionState.ABSTRACTING,
            SessionState.FAILED,
        ],
        SessionState.ABSTRACTING: [
            SessionState.GENERATING,
            SessionState.FAILED,
        ],
        SessionState.GENERATING: [
            SessionState.DOCUMENTING,
            SessionState.FAILED,
        ],
        SessionState.DOCUMENTING: [
            SessionState.REVIEW_READY,
            SessionState.FAILED,
        ],
        SessionState.REVIEW_READY: [],  # Terminal state
        SessionState.FAILED: [
            SessionState.QUEUED,  # retry_step
        ],
    }

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        brief_repository: BriefRepositoryPort,
        decision_repository: DecisionLogRepositoryPort,
        conversation_port: ConversationPort,
        asset_port: AssetPort,
    ):
        """Initialize orchestrator with dependencies.

        Args:
            session_repository: Repository for session persistence
            brief_repository: Repository for brief persistence
            decision_repository: Repository for decision log persistence
            conversation_port: Port for creating conversations
            asset_port: Port for handling sketch uploads
        """
        self._session_repository = session_repository
        self._brief_repository = brief_repository
        self._decision_repository = decision_repository
        self._conversation_port = conversation_port
        self._asset_port = asset_port

    async def create_session(
        self,
        project_id: UUID,
        user_id: UUID,
        tenant_id: str,
        workspace_id: UUID,
        purpose: str,
        mode: ExecutionMode = ExecutionMode.GUIDED,
    ) -> DesignSession:
        """Create a new design session.

        Args:
            project_id: Project UUID
            user_id: User UUID
            tenant_id: Tenant string ID
            workspace_id: Workspace UUID
            purpose: User's design purpose
            mode: Execution mode (auto or guided)

        Returns:
            Created DesignSession entity

        Raises:
            ValueError: If state transition is invalid
        """
        from apps.design_sessions.domain.value_objects import SessionMode, SessionStatus, PipelineStep

        session_mode = SessionMode.GUIDED if mode == ExecutionMode.GUIDED else SessionMode.AUTO

        session = DesignSession(
            project_id=project_id,
            started_by=user_id,
            mode=session_mode,
            status=SessionStatus.QUEUED,
            current_step=PipelineStep.PURPOSE_INPUT,
        )

        saved_session = await self._session_repository.save(session)

        brief = DesignBrief(
            session_id=saved_session.id,
            purpose=purpose,
            audience="",
            usage_context="",
            constraints="",
            result_form="",
        )
        await self._brief_repository.save(brief)

        await self._conversation_port.create_conversation(
            session_id=saved_session.id,
            user_id=user_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
        )

        decision = DecisionLog(
            session_id=saved_session.id,
            step=PipelineStep.PURPOSE_INPUT,
            action="create",
            actor_kind="user",
            actor_id=user_id,
            rationale="Session created with purpose",
        )
        await self._decision_repository.save(decision)

        return saved_session

    async def transition_session(
        self,
        session_id: UUID,
        new_state: SessionState,
        actor: str,
        rationale: str,
        decision_data: Optional[Dict] = None,
    ) -> DesignSession:
        """Transition session to new state.

        Args:
            session_id: Session UUID
            new_state: Target state
            actor: Who made the decision ('user' or 'auto')
            rationale: Reason for transition
            decision_data: Additional decision data

        Returns:
            Updated DesignSession entity

        Raises:
            ValueError: If transition is invalid
        """
        # Get current session
        session = await self._session_repository.get_by_id(session_id)

        if session is None:
            raise ValueError(f'Session {session_id} not found')

        # Validate transition
        current_state = SessionState(session.status.value)
        if new_state not in self._VALID_TRANSITIONS.get(current_state, []):
            raise ValueError(
                f'Invalid transition from {current_state.value} to {new_state.value}'
            )

        # Update session state
        session.status = SessionStatus(new_state.value)

        # Update step based on state mapping (SPEC-01 §5.4)
        session.current_step = self._map_state_to_step(new_state)

        # Save updated session
        updated_session = await self._session_repository.save(session)

        decision = DecisionLog(
            session_id=session_id,
            step=session.current_step,
            action="transition",
            actor_kind=actor,
            actor_id=UUID("00000000-0000-0000-0000-000000000000") if actor == "auto" else session.started_by,
            rationale=rationale,
        )
        await self._decision_repository.save(decision)

        return updated_session

    async def execute_step(
        self,
        session_id: UUID,
    ) -> DesignSession:
        """Execute current step (auto mode only).

        In auto mode, dispatches a Celery task for async step execution.
        In guided mode, waits for user input.

        Args:
            session_id: Session UUID

        Returns:
            Updated DesignSession entity

        Raises:
            ValueError: If session is not in auto mode
            OperationError: If task dispatch fails
        """
        session = await self._session_repository.get_by_id(session_id)

        if session is None:
            raise ValueError(f'Session {session_id} not found')

        if session.mode != SessionMode.AUTO:
            raise ValueError('Step execution only available in auto mode')

        from apps.design_sessions.infrastructure.tasks import execute_session_step_task

        try:
            # Submit task to Celery for async execution
            task = execute_session_step_task.delay(
                session_id=str(session_id),
                step=session.current_step.value,
            )

            logger.info(
                f"Dispatched Celery task {task.id} for session {session_id} "
                f"step {session.current_step.value}"
            )

            # Note: Session will be updated asynchronously by the task
            # Return current session state (task will update it in background)
            return session

        except Exception as e:
            # Task dispatch failed - transition to failed state
            logger.error(f"Failed to dispatch Celery task for session {session_id}: {e}")

            await self.handle_step_failure(
                session_id=session_id,
                error_message=f"Failed to dispatch execution task: {str(e)}",
                step=session.current_step.value,
            )

            raise OperationError(
                "execute_step",
                f"Failed to dispatch Celery task: {e}"
            )

    async def handle_step_failure(
        self,
        session_id: UUID,
        error_message: str,
        step: int | PipelineStep,
    ) -> DesignSession:
        """Handle step failure by transitioning to failed state.

        Args:
            session_id: Session UUID
            error_message: Error description
            step: Step number that failed

        Returns:
            Updated DesignSession in FAILED state
        """
        session = await self._session_repository.get_by_id(session_id)

        if session is None:
            raise ValueError(f'Session {session_id} not found')

        # Transition to failed state
        session = await self.transition_session(
            session_id=session_id,
            new_state=SessionState.FAILED,
            actor='auto',
            rationale=f'Step {step} failed: {error_message}',
            decision_data={'step': step, 'error': error_message},
        )

        return session

    async def retry_step(
        self,
        session_id: UUID,
    ) -> DesignSession:
        """Retry a failed session from queued state.

        Args:
            session_id: Session UUID

        Returns:
            Updated DesignSession in QUEUED state

        Raises:
            ValueError: If session is not in FAILED state
        """
        session = await self._session_repository.get_by_id(session_id)

        if session is None:
            raise ValueError(f'Session {session_id} not found')

        if session.status != SessionStatus.FAILED:
            raise ValueError('Can only retry from FAILED state')
            raise ValueError('Can only retry from FAILED state')

        # Transition back to queued
        session = await self.transition_session(
            session_id=session_id,
            new_state=SessionState.QUEUED,
            actor='user',
            rationale='Retrying failed session',
        )

        return session

    def _map_state_to_step(self, state: SessionState) -> PipelineStep:
        """Map state to pipeline step (SPEC-01 §5.4)."""
        state_to_step = {
            SessionState.QUEUED: PipelineStep.PURPOSE_INPUT,
            SessionState.RESEARCHING: PipelineStep.TREND_RESEARCH,
            SessionState.CONCEPTING: PipelineStep.CONCEPT_GENERATION,
            SessionState.REFERENCING: PipelineStep.REFERENCE_SEARCH,
            SessionState.ABSTRACTING: PipelineStep.SKETCH_ANALYSIS,
            SessionState.GENERATING: PipelineStep.GENERATION,
            SessionState.DOCUMENTING: PipelineStep.SPEC_DOCUMENT,
            SessionState.REVIEW_READY: PipelineStep.REVIEW,
            SessionState.FAILED: PipelineStep.PURPOSE_INPUT,
        }

        return state_to_step.get(state, PipelineStep.PURPOSE_INPUT)

    def _get_next_state(self, current_state: SessionState) -> Optional[SessionState]:
        """Get next state in pipeline.

        Args:
            current_state: Current session state

        Returns:
            Next state or None if terminal
        """
        # Define pipeline order
        pipeline_order = [
            SessionState.QUEUED,
            SessionState.RESEARCHING,
            SessionState.CONCEPTING,
            SessionState.REFERENCING,
            SessionState.ABSTRACTING,
            SessionState.GENERATING,
            SessionState.DOCUMENTING,
            SessionState.REVIEW_READY,
        ]

        try:
            current_index = pipeline_order.index(current_state)
            if current_index + 1 < len(pipeline_order):
                return pipeline_order[current_index + 1]
        except ValueError:
            pass

        return None
