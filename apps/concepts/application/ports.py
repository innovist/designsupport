"""Application ports for concepts module.

Defines interfaces for external dependencies including cross-module ports.
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from apps.concepts.domain.entities import ConceptCandidate, ConceptDecision


class ConceptRepositoryPort(ABC):
    """Repository port for ConceptCandidate entities."""

    @abstractmethod
    async def save(self, concept: ConceptCandidate) -> ConceptCandidate:
        """Save a concept candidate.

        Args:
            concept: Concept entity to save

        Returns:
            Saved concept with assigned ID if new
        """
        pass

    @abstractmethod
    async def get_by_id(self, concept_id: UUID) -> Optional[ConceptCandidate]:
        """Get concept by ID.

        Args:
            concept_id: Concept UUID

        Returns:
            ConceptCandidate if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_session(self, session_id: UUID) -> list[ConceptCandidate]:
        """List all concepts for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of ConceptCandidate entities
        """
        pass

    @abstractmethod
    async def delete(self, concept_id: UUID) -> None:
        """Delete a concept by ID.

        Args:
            concept_id: Concept UUID
        """
        pass


class DecisionRepositoryPort(ABC):
    """Repository port for ConceptDecision entities."""

    @abstractmethod
    async def save(self, decision: ConceptDecision) -> ConceptDecision:
        """Save a concept decision.

        Args:
            decision: Decision entity to save

        Returns:
            Saved decision with assigned ID if new
        """
        pass

    @abstractmethod
    async def list_by_concept(self, concept_id: UUID) -> list[ConceptDecision]:
        """List all decisions for a concept.

        Args:
            concept_id: Concept UUID

        Returns:
            List of ConceptDecision entities
        """
        pass


class SessionPort(ABC):
    """Port for accessing design sessions (from design_sessions module)."""

    @abstractmethod
    async def get_session_brief(self, session_id: UUID) -> Optional[dict]:
        """Get brief data for a session.

        Args:
            session_id: Session UUID

        Returns:
            Dict with brief data including keywords, tone, target_audience
            or None if session not found
        """
        pass

    @abstractmethod
    async def session_exists(self, session_id: UUID) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session UUID

        Returns:
            True if session exists, False otherwise
        """
        pass


class TrendInsightPort(ABC):
    """Port for accessing trend insights (from trend_knowledge module)."""

    @abstractmethod
    async def insights_exist(self, insight_ids: list[UUID]) -> bool:
        """Check if trend insights exist.

        Args:
            insight_ids: List of insight UUIDs

        Returns:
            True if all insights exist, False otherwise
        """
        pass


class ReferenceAnalysisPort(ABC):
    """Port for accessing reference analyses (from references module)."""

    @abstractmethod
    async def analyses_exist(self, analysis_ids: list[UUID]) -> bool:
        """Check if reference analyses exist.

        Args:
            analysis_ids: List of analysis UUIDs

        Returns:
            True if all analyses exist, False otherwise
        """
        pass
