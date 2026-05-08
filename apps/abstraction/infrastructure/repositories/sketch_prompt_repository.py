"""Repository implementation for SketchPrompt entities."""
from typing import Optional
from uuid import UUID

from apps.abstraction.application.ports import SketchPromptRepositoryPort
from apps.abstraction.domain.entities import SketchPrompt
from apps.abstraction.infrastructure.orm.models import SketchPromptModel


class DjangoSketchPromptRepository(SketchPromptRepositoryPort):
    """Django ORM implementation of SketchPrompt repository."""

    async def save(self, prompt: SketchPrompt) -> SketchPrompt:
        """Save a sketch prompt."""
        orm_prompt = SketchPromptModel.from_domain(prompt)

        # Check if it's an update or create
        existing = await self._get_model_by_id(prompt.id)
        if existing:
            # Update existing
            existing.kind = orm_prompt.kind
            existing.template = orm_prompt.template
            existing.variables = orm_prompt.variables
            existing.source_refs = orm_prompt.source_refs
            existing.save()
        else:
            # Create new
            orm_prompt.save()

        return orm_prompt.to_domain()

    async def get_by_id(self, prompt_id: UUID) -> Optional[SketchPrompt]:
        """Get prompt by ID."""
        orm_prompt = await self._get_model_by_id(prompt_id)
        if orm_prompt:
            return orm_prompt.to_domain()
        return None

    async def list_by_session(self, session_id: UUID) -> list[SketchPrompt]:
        """List all prompts for a session."""
        orm_prompts = SketchPromptModel.objects.filter(
            session_id=str(session_id)
        ).order_by('-created_at')

        return [prompt.to_domain() for prompt in orm_prompts]

    async def delete(self, prompt_id: UUID) -> None:
        """Delete a prompt by ID."""
        SketchPromptModel.objects.filter(id=str(prompt_id)).delete()

    async def _get_model_by_id(self, prompt_id: UUID) -> Optional[SketchPromptModel]:
        """Helper to get ORM model by ID."""
        try:
            return SketchPromptModel.objects.get(id=str(prompt_id))
        except SketchPromptModel.DoesNotExist:
            return None
