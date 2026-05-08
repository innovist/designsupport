"""Repository implementations for prompt library."""
from typing import Optional
from uuid import UUID

from asgiref.sync import sync_to_async

from apps.prompt_library.application.ports import (
    PromptPatternRepositoryPort,
    PromptSafetyViolationRepositoryPort,
)
from apps.prompt_library.domain import PromptPattern, PromptSafetyViolation
from apps.prompt_library.infrastructure.orm.models import (
    PromptPatternModel,
    PromptSafetyViolationModel,
)


class DjangoPromptPatternRepository(PromptPatternRepositoryPort):
    """Django ORM implementation of PromptPatternRepositoryPort.

    REQ-03-PROMPT-002: Search patterns by category and domain.
    """

    async def list_active(self) -> list[PromptPattern]:
        """Get all active prompt patterns."""
        queryset = PromptPatternModel.objects.filter(active=True).order_by("category", "name")
        models = await sync_to_async(list)(queryset)
        return [model.to_domain() for model in models]

    async def search_by_category(self, category: str) -> list[PromptPattern]:
        """Search patterns by category."""
        queryset = PromptPatternModel.objects.filter(
            category=category,
            active=True,
        ).order_by("name")
        models = await sync_to_async(list)(queryset)
        return [model.to_domain() for model in models]

    async def search_by_domain_tags(self, tags: list[str]) -> list[PromptPattern]:
        """Search patterns by domain tags."""
        tag_set = set(tags)
        queryset = PromptPatternModel.objects.filter(active=True).order_by("category", "name")
        models = await sync_to_async(list)(queryset)
        return [
            model.to_domain()
            for model in models
            if tag_set.intersection(set(model.domain_tags or []))
        ]

    async def get_by_id(self, pattern_id: UUID) -> Optional[PromptPattern]:
        """Get pattern by ID."""
        try:
            model = await PromptPatternModel.objects.aget(id=pattern_id)
            return model.to_domain()
        except PromptPatternModel.DoesNotExist:
            return None

    async def save(self, entity: PromptPattern) -> PromptPattern:
        """Save a pattern entity."""
        model = PromptPatternModel.from_domain(entity)
        await sync_to_async(model.save)()
        return model.to_domain()

    async def delete(self, entity_id: UUID) -> None:
        """Delete a pattern by ID."""
        await sync_to_async(PromptPatternModel.objects.filter(id=entity_id).delete)()


class DjangoPromptSafetyViolationRepository(PromptSafetyViolationRepositoryPort):
    """Django ORM implementation of PromptSafetyViolationRepositoryPort.

    REQ-03-PROMPT-006: Record safety violations for auditing.
    """

    async def list_by_session(self, session_id: UUID) -> list[PromptSafetyViolation]:
        """Get all violations for a session."""
        queryset = PromptSafetyViolationModel.objects.filter(
            session_id=session_id,
        ).order_by("-created_at")
        models = await sync_to_async(list)(queryset)
        return [model.to_domain() for model in models]

    async def list_by_prompt(self, prompt_id: UUID) -> list[PromptSafetyViolation]:
        """Get all violations for a specific prompt."""
        queryset = PromptSafetyViolationModel.objects.filter(
            prompt_id=prompt_id,
        ).order_by("-created_at")
        models = await sync_to_async(list)(queryset)
        return [model.to_domain() for model in models]

    async def save(self, entity: PromptSafetyViolation) -> PromptSafetyViolation:
        """Save a violation entity."""
        model = PromptSafetyViolationModel.from_domain(entity)
        await sync_to_async(model.save)()
        return model.to_domain()

    async def delete(self, entity_id: UUID) -> None:
        """Delete a violation by ID."""
        await sync_to_async(PromptSafetyViolationModel.objects.filter(id=entity_id).delete)()
