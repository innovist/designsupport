"""Repository implementation for AbstractionRule entities."""
from typing import Optional
from uuid import UUID

from django.db.models import Q

from apps.abstraction.application.ports import AbstractionRuleRepositoryPort
from apps.abstraction.domain.entities import AbstractionRule
from apps.abstraction.infrastructure.orm.models import AbstractionRuleModel


class DjangoAbstractionRuleRepository(AbstractionRuleRepositoryPort):
    """Django ORM implementation of AbstractionRule repository."""

    async def save(self, rule: AbstractionRule) -> AbstractionRule:
        """Save an abstraction rule."""
        orm_rule = AbstractionRuleModel.from_domain(rule)

        # Check if it's an update or create
        existing = await self._get_model_by_id(rule.id)
        if existing:
            # Update existing
            existing.axis = orm_rule.axis
            existing.observation = orm_rule.observation
            existing.applied_rule = orm_rule.applied_rule
            existing.source_refs = orm_rule.source_refs
            existing.risk_note = orm_rule.risk_note
            existing.save()
        else:
            # Create new
            orm_rule.save()

        return orm_rule.to_domain()

    async def get_by_id(self, rule_id: UUID) -> Optional[AbstractionRule]:
        """Get rule by ID."""
        orm_rule = await self._get_model_by_id(rule_id)
        if orm_rule:
            return orm_rule.to_domain()
        return None

    async def list_by_concept(self, concept_id: UUID) -> list[AbstractionRule]:
        """List all rules for a concept."""
        orm_rules = AbstractionRuleModel.objects.filter(
            concept_id=str(concept_id)
        ).order_by('-created_at')

        return [rule.to_domain() for rule in orm_rules]

    async def list_by_session(self, session_id: UUID) -> list[AbstractionRule]:
        """List all rules for a session."""
        orm_rules = AbstractionRuleModel.objects.filter(
            session_id=str(session_id)
        ).order_by('-created_at')

        return [rule.to_domain() for rule in orm_rules]

    async def delete(self, rule_id: UUID) -> None:
        """Delete a rule by ID."""
        AbstractionRuleModel.objects.filter(id=str(rule_id)).delete()

    async def _get_model_by_id(self, rule_id: UUID) -> Optional[AbstractionRuleModel]:
        """Helper to get ORM model by ID."""
        try:
            return AbstractionRuleModel.objects.get(id=str(rule_id))
        except AbstractionRuleModel.DoesNotExist:
            return None
