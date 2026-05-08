"""Django ORM repository for DecisionLog aggregate."""
from typing import List
from uuid import UUID

from apps.design_sessions.application.ports import DecisionLogRepositoryPort
from apps.design_sessions.domain.entities import DecisionLog, PipelineStep
from apps.design_sessions.infrastructure.orm import models as orm


class DjangoDecisionLogRepository(DecisionLogRepositoryPort):
    """Django ORM implementation of DecisionLogRepositoryPort."""

    async def list_by_session(self, session_id: UUID) -> List[DecisionLog]:
        results = []
        async for obj in orm.DecisionLog.objects.filter(session_id=session_id).order_by("created_at"):
            results.append(self._to_entity(obj))
        return results

    async def save(self, decision: DecisionLog) -> DecisionLog:
        defaults = {
            "session_id": decision.session_id,
            "step": decision.step.value,
            "action": decision.action,
            "actor_kind": decision.actor_kind,
            "actor_id": decision.actor_id,
            "rationale": decision.rationale,
            "evidence_refs": decision.evidence_refs,
        }
        obj, _ = await orm.DecisionLog.objects.aupdate_or_create(
            id=decision.id,
            defaults=defaults,
        )
        return self._to_entity(obj)

    @staticmethod
    def _to_entity(obj: orm.DecisionLog) -> DecisionLog:
        return DecisionLog(
            session_id=obj.session_id,
            step=PipelineStep(obj.step),
            action=obj.action,
            actor_kind=obj.actor_kind,
            actor_id=obj.actor_id,
            rationale=obj.rationale,
            evidence_refs=obj.evidence_refs or [],
            id=obj.id,
            created_at=obj.created_at,
        )
