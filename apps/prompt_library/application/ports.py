"""Repository ports for prompt library application layer."""
from abc import abstractmethod
from typing import Optional
from uuid import UUID

from shared.application.ports import RepositoryPort

from apps.prompt_library.domain import PromptPattern, PromptSafetyViolation


class PromptPatternRepositoryPort(RepositoryPort[PromptPattern]):
    """Repository port for prompt patterns.

    REQ-03-PROMPT-002: Search patterns by category and domain.
    """

    @abstractmethod
    async def list_active(self) -> list[PromptPattern]:
        """Get all active prompt patterns.

        Returns:
            List of active patterns sorted by category
        """
        pass

    @abstractmethod
    async def search_by_category(
        self,
        category: str,
    ) -> list[PromptPattern]:
        """Search patterns by category.

        Args:
            category: PromptCategory enum value

        Returns:
            List of matching active patterns
        """
        pass

    @abstractmethod
    async def search_by_domain_tags(
        self,
        tags: list[str],
    ) -> list[PromptPattern]:
        """Search patterns by domain tags.

        Args:
            tags: List of domain tags to match

        Returns:
            List of patterns matching any of the tags
        """
        pass

    @abstractmethod
    async def get_by_id(self, pattern_id: UUID) -> Optional[PromptPattern]:
        """Get pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern if found, None otherwise
        """
        pass


class PromptSafetyViolationRepositoryPort(RepositoryPort[PromptSafetyViolation]):
    """Repository port for prompt safety violations.

    REQ-03-PROMPT-006: Record safety violations for auditing.
    """

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> list[PromptSafetyViolation]:
        """Get all violations for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of violations for the session
        """
        pass

    @abstractmethod
    async def list_by_prompt(self, prompt_id: UUID) -> list[PromptSafetyViolation]:
        """Get all violations for a specific prompt.

        Args:
            prompt_id: Prompt identifier

        Returns:
            List of violations for the prompt
        """
        pass
