"""Application ports for specs module.

Defines interfaces for external dependencies including cross-module ports.
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from apps.specs.domain.entities import DomainPack, SpecDocument


class SpecDocumentRepositoryPort(ABC):
    """Repository port for SpecDocument entities."""

    @abstractmethod
    async def save(self, spec: SpecDocument) -> SpecDocument:
        """Save a spec document.

        Args:
            spec: Spec entity to save

        Returns:
            Saved spec with assigned ID if new
        """
        pass

    @abstractmethod
    async def get_by_id(self, spec_id: UUID) -> Optional[SpecDocument]:
        """Get spec by ID.

        Args:
            spec_id: Spec UUID

        Returns:
            SpecDocument if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_session(self, session_id: UUID) -> Optional[SpecDocument]:
        """Get latest approved spec for a session.

        Args:
            session_id: Session UUID

        Returns:
            Latest approved SpecDocument if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all_versions(self, session_id: UUID) -> list[SpecDocument]:
        """List all versions of specs for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of SpecDocument entities ordered by version
        """
        pass

    @abstractmethod
    async def list_by_status(self, status: str) -> list[SpecDocument]:
        """List specs by status.

        Args:
            status: Status string (e.g., "in_review", "approved")

        Returns:
            List of SpecDocument entities
        """
        pass


SpecRepositoryPort = SpecDocumentRepositoryPort


class DomainPackRepositoryPort(ABC):
    """Repository port for DomainPack entities."""

    @abstractmethod
    async def get_by_id(self, pack_id: str) -> Optional[DomainPack]:
        """Get domain pack by ID.

        Args:
            pack_id: Domain pack ID (e.g., "industrial")

        Returns:
            DomainPack if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(self) -> list[DomainPack]:
        """List all domain packs.

        Returns:
            List of DomainPack entities
        """
        pass

    @abstractmethod
    async def exists(self, pack_id: str) -> bool:
        """Check if domain pack exists.

        Args:
            pack_id: Domain pack ID

        Returns:
            True if exists, False otherwise
        """
        pass


class ConceptPort(ABC):
    """Port for accessing concept candidates and decisions (from concepts module)."""

    @abstractmethod
    async def get_concepts_by_session(self, session_id: UUID) -> list[dict]:
        """Get all concepts for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of concept data including decisions
        """
        pass

    @abstractmethod
    async def get_adopted_concept(self, session_id: UUID) -> Optional[dict]:
        """Get the adopted concept for a session.

        Args:
            session_id: Session UUID

        Returns:
            Adopted concept data if found, None otherwise
        """
        pass


class AbstractionRulePort(ABC):
    """Port for accessing abstraction rules (from abstraction module)."""

    @abstractmethod
    async def get_rules_by_session(self, session_id: UUID) -> list[dict]:
        """Get all abstraction rules for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of abstraction rule data
        """
        pass


class GenerationJobPort(ABC):
    """Port for accessing generation jobs and designs (from generation module)."""

    @abstractmethod
    async def get_jobs_by_session(self, session_id: UUID) -> list[dict]:
        """Get all generation jobs for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of generation job data including design references
        """
        pass

    @abstractmethod
    async def get_designs_by_job(self, job_id: UUID) -> list[dict]:
        """Get all designs for a generation job.

        Args:
            job_id: Generation job UUID

        Returns:
            List of design data with full traceability metadata
        """
        pass


class SessionPort(ABC):
    """Port for accessing design sessions (from design_sessions module)."""

    @abstractmethod
    async def get_session(self, session_id: UUID) -> Optional[dict]:
        """Get session data.

        Args:
            session_id: Session UUID

        Returns:
            Session data including brief, domain, user info
        """
        pass

    @abstractmethod
    async def session_exists(self, session_id: UUID) -> bool:
        """Check if session exists.

        Args:
            session_id: Session UUID

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_session_brief(self, session_id: UUID) -> Optional[dict]:
        """Get brief data for a session.

        Args:
            session_id: Session UUID

        Returns:
            Brief data dictionary
        """
        pass

    @abstractmethod
    async def get_session_domain(self, session_id: UUID) -> Optional[str]:
        """Get domain for a session.

        Args:
            session_id: Session UUID

        Returns:
            Domain identifier if found, None otherwise
        """
        pass
