"""Application ports for abstraction module.

Defines interfaces for external dependencies including cross-module ports.
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from apps.abstraction.domain.entities import (
    AbstractionRule,
    SketchPrompt,
    PromptPattern,
    PromptSafetyViolation,
)


class AbstractionRuleRepositoryPort(ABC):
    """Repository port for AbstractionRule entities."""

    @abstractmethod
    async def save(self, rule: AbstractionRule) -> AbstractionRule:
        """Save an abstraction rule.

        Args:
            rule: AbstractionRule entity to save

        Returns:
            Saved rule with assigned ID if new
        """
        pass

    @abstractmethod
    async def get_by_id(self, rule_id: UUID) -> Optional[AbstractionRule]:
        """Get rule by ID.

        Args:
            rule_id: Rule UUID

        Returns:
            AbstractionRule if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_concept(self, concept_id: UUID) -> list[AbstractionRule]:
        """List all rules for a concept.

        Args:
            concept_id: Concept UUID

        Returns:
            List of AbstractionRule entities
        """
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> list[AbstractionRule]:
        """List all rules for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of AbstractionRule entities
        """
        pass

    @abstractmethod
    async def delete(self, rule_id: UUID) -> None:
        """Delete a rule by ID.

        Args:
            rule_id: Rule UUID
        """
        pass


class SketchPromptRepositoryPort(ABC):
    """Repository port for SketchPrompt entities."""

    @abstractmethod
    async def save(self, prompt: SketchPrompt) -> SketchPrompt:
        """Save a sketch prompt.

        Args:
            prompt: SketchPrompt entity to save

        Returns:
            Saved prompt with assigned ID if new
        """
        pass

    @abstractmethod
    async def get_by_id(self, prompt_id: UUID) -> Optional[SketchPrompt]:
        """Get prompt by ID.

        Args:
            prompt_id: Prompt UUID

        Returns:
            SketchPrompt if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> list[SketchPrompt]:
        """List all prompts for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of SketchPrompt entities
        """
        pass

    @abstractmethod
    async def delete(self, prompt_id: UUID) -> None:
        """Delete a prompt by ID.

        Args:
            prompt_id: Prompt UUID
        """
        pass


class PromptPatternRepositoryPort(ABC):
    """Repository port for PromptPattern entities."""

    @abstractmethod
    async def save(self, pattern: PromptPattern) -> PromptPattern:
        """Save a prompt pattern.

        Args:
            pattern: PromptPattern entity to save

        Returns:
            Saved pattern with assigned ID if new
        """
        pass

    @abstractmethod
    async def get_by_id(self, pattern_id: UUID) -> Optional[PromptPattern]:
        """Get pattern by ID.

        Args:
            pattern_id: Pattern UUID

        Returns:
            PromptPattern if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_active(self) -> list[PromptPattern]:
        """List all active patterns.

        Returns:
            List of active PromptPattern entities
        """
        pass

    @abstractmethod
    async def list_by_category(self, category: str) -> list[PromptPattern]:
        """List all patterns by category.

        Args:
            category: Category name

        Returns:
            List of PromptPattern entities
        """
        pass

    @abstractmethod
    async def delete(self, pattern_id: UUID) -> None:
        """Delete a pattern by ID.

        Args:
            pattern_id: Pattern UUID
        """
        pass


class PromptSafetyViolationRepositoryPort(ABC):
    """Repository port for PromptSafetyViolation entities."""

    @abstractmethod
    async def save(self, violation: PromptSafetyViolation) -> PromptSafetyViolation:
        """Save a safety violation.

        Args:
            violation: PromptSafetyViolation entity to save

        Returns:
            Saved violation with assigned ID if new
        """
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> list[PromptSafetyViolation]:
        """List all violations for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of PromptSafetyViolation entities
        """
        pass


class ConceptPort(ABC):
    """Port for accessing concept candidates (from concepts module)."""

    @abstractmethod
    async def get_by_id(self, concept_id: UUID) -> Optional[dict]:
        """Get concept by ID.

        Args:
            concept_id: Concept UUID

        Returns:
            Dict with concept data or None if not found
        """
        pass

    @abstractmethod
    async def concept_exists(self, concept_id: UUID) -> bool:
        """Check if a concept exists.

        Args:
            concept_id: Concept UUID

        Returns:
            True if concept exists, False otherwise
        """
        pass


class SketchAnalysisPort(ABC):
    """Port for accessing sketch analysis data (from sketch_analysis module)."""

    @abstractmethod
    async def get_latest_by_session(self, session_id: UUID) -> Optional[dict]:
        """Get latest sketch analysis for a session.

        Args:
            session_id: Session UUID

        Returns:
            Dict with sketch analysis data including:
            - keep_elements: List[str] - Elements to preserve
            - modifiable_elements: List[str] - Elements that can be modified
            - core_identity: str - Core concept identity
            or None if not found
        """
        pass
