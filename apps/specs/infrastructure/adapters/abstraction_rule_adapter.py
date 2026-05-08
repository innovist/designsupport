"""Django ORM adapter for AbstractionRule port.

Implements AbstractionRulePort from abstraction module.
"""
from uuid import UUID

from apps.specs.application.ports import AbstractionRulePort


class DjangoORMAbstractionRuleAdapter(AbstractionRulePort):
    """Django ORM adapter for accessing abstraction rules."""

    async def get_rules_by_session(self, session_id: UUID) -> list[dict]:
        """Get all abstraction rules for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of abstraction rule data
        """
        from apps.abstraction.infrastructure.orm.models import AbstractionRuleModel

        rules = AbstractionRuleModel.objects.filter(session_id=str(session_id)).order_by("axis", "-created_at")
        return [
            {
                "id": str(rule.id),
                "session_id": str(rule.session_id),
                "concept_id": str(rule.concept_id),
                "axis": rule.axis,
                "observation": rule.observation,
                "applied_rule": rule.applied_rule,
                "source_refs": rule.source_refs,
                "risk_note": rule.risk_note,
                "created_at": rule.created_at.isoformat(),
            }
            async for rule in rules
        ]
