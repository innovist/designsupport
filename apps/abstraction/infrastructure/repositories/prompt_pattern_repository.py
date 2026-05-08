"""Repository implementation for PromptPattern entities."""
from typing import Optional
from uuid import UUID

from apps.abstraction.application.ports import PromptPatternRepositoryPort
from apps.abstraction.domain.entities import PromptPattern
from apps.abstraction.infrastructure.orm.models import PromptPatternModel


class DjangoPromptPatternRepository(PromptPatternRepositoryPort):
    """Django ORM implementation of PromptPattern repository."""

    async def save(self, pattern: PromptPattern) -> PromptPattern:
        """Save a prompt pattern."""
        orm_pattern = PromptPatternModel.from_domain(pattern)

        # Check if it's an update or create
        existing = await self._get_model_by_id(pattern.id)
        if existing:
            # Update existing
            existing.name = orm_pattern.name
            existing.category = orm_pattern.category
            existing.source_reference = orm_pattern.source_reference
            existing.input_slots = orm_pattern.input_slots
            existing.output_constraints = orm_pattern.output_constraints
            existing.safety_rules = orm_pattern.safety_rules
            existing.domain_tags = orm_pattern.domain_tags
            existing.active = orm_pattern.active
            existing.save()
        else:
            # Create new
            orm_pattern.save()

        return orm_pattern.to_domain()

    async def get_by_id(self, pattern_id: UUID) -> Optional[PromptPattern]:
        """Get pattern by ID."""
        orm_pattern = await self._get_model_by_id(pattern_id)
        if orm_pattern:
            return orm_pattern.to_domain()
        return None

    async def list_active(self) -> list[PromptPattern]:
        """List all active patterns."""
        orm_patterns = PromptPatternModel.objects.filter(
            active=True
        ).order_by('name')

        return [pattern.to_domain() for pattern in orm_patterns]

    async def list_by_category(self, category: str) -> list[PromptPattern]:
        """List all patterns by category."""
        orm_patterns = PromptPatternModel.objects.filter(
            category=category
        ).order_by('name')

        return [pattern.to_domain() for pattern in orm_patterns]

    async def delete(self, pattern_id: UUID) -> None:
        """Delete a pattern by ID."""
        PromptPatternModel.objects.filter(id=str(pattern_id)).delete()

    async def _get_model_by_id(self, pattern_id: UUID) -> Optional[PromptPatternModel]:
        """Helper to get ORM model by ID."""
        try:
            return PromptPatternModel.objects.get(id=str(pattern_id))
        except PromptPatternModel.DoesNotExist:
            return None
