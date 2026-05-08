"""RecordDecision use case.

REQ-01-ORCH-006: User and auto decisions share the same schema.
"""
from typing import List, Optional
from uuid import UUID

from apps.design_sessions.application.ports import DecisionLogRepositoryPort
from apps.design_sessions.domain.entities import DecisionLog, PipelineStep
from shared.application.decorators.audit import audit
from shared.domain.exceptions import ValidationError


@audit(
    "design_session.record_decision",
    target_type_extractor=lambda **kw: "DecisionLog",
    target_id_extractor=lambda **kw: str(kw.get("session_id", "")),
)
class RecordDecisionUseCase:
    """Record a decision (user or auto) for a design session step."""

    def __init__(self, decision_repository: DecisionLogRepositoryPort) -> None:
        self._decision_repo = decision_repository

    async def execute(
        self,
        session_id: UUID,
        step: int,
        action: str,
        actor_kind: str,
        actor_id: UUID,
        rationale: str,
        evidence_refs: Optional[List[dict]] = None,
    ) -> DecisionLog:
        """Record a decision log entry.

        Args:
            session_id: Session UUID
            step: Pipeline step number (1-17)
            action: Action description
            actor_kind: "user" or "auto"
            actor_id: UUID of actor
            rationale: Reason for decision
            evidence_refs: Supporting evidence refs

        Returns:
            Saved DecisionLog entity

        Raises:
            ValidationError: If actor_kind invalid or step out of range
        """
        if actor_kind not in {"user", "auto"}:
            raise ValidationError(field="actor_kind", message=f"Must be 'user' or 'auto', got {actor_kind!r}")
        if not (1 <= step <= 17):
            raise ValidationError(field="step", message=f"Must be 1-17, got {step}")

        try:
            pipeline_step = PipelineStep(step)
        except ValueError:
            raise ValidationError(field="step", message=f"Invalid step: {step}")

        decision = DecisionLog(
            session_id=session_id,
            step=pipeline_step,
            action=action,
            actor_kind=actor_kind,
            actor_id=actor_id,
            rationale=rationale,
            evidence_refs=evidence_refs or [],
        )
        return await self._decision_repo.save(decision)
