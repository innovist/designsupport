"""Django ORM repository for DesignBrief aggregate."""
from typing import Optional
from uuid import UUID

from apps.design_sessions.application.ports import BriefRepositoryPort
from apps.design_sessions.domain.entities import DesignBrief
from apps.design_sessions.infrastructure.orm import models as orm


class DjangoBriefRepository(BriefRepositoryPort):
    """Django ORM implementation of BriefRepositoryPort."""

    async def get_by_session(self, session_id: UUID) -> Optional[DesignBrief]:
        try:
            obj = await orm.DesignBrief.objects.aget(session_id=session_id)
            return self._to_entity(obj)
        except orm.DesignBrief.DoesNotExist:
            return None

    async def save(self, brief: DesignBrief) -> DesignBrief:
        defaults = {
            "purpose": brief.purpose,
            "audience": brief.audience,
            "usage_context": brief.usage_context,
            "constraints": brief.constraints,
            "result_form": brief.result_form,
            "clarifying_questions": brief.clarifying_questions,
            "score": brief.score,
        }
        obj, _ = await orm.DesignBrief.objects.aupdate_or_create(
            id=brief.id,
            defaults={**defaults, "session_id": brief.session_id},
        )
        return self._to_entity(obj)

    @staticmethod
    def _to_entity(obj: orm.DesignBrief) -> DesignBrief:
        return DesignBrief(
            session_id=obj.session_id,
            purpose=obj.purpose,
            audience=obj.audience,
            usage_context=obj.usage_context,
            constraints=obj.constraints,
            result_form=obj.result_form,
            clarifying_questions=obj.clarifying_questions or [],
            score=obj.score,
            id=obj.id,
        )
