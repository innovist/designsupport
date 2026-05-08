"""Ports (interfaces) for generation module.

Defines the contracts that infrastructure layer must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from apps.generation.domain.entities import GenerationJob, GeneratedDesign, CostMetadata
from apps.generation.domain.value_objects import GenerationKind, GenerationStatus
from shared.application.result import Result


class GenerationJobRepositoryPort(ABC):
    """Repository port for GenerationJob entities."""

    @abstractmethod
    async def save(self, job: GenerationJob) -> Result[GenerationJob]:
        """Save a generation job.

        Args:
            job: The job to save

        Returns:
            Result containing the saved job
        """
        pass

    @abstractmethod
    async def find_by_id(self, job_id: UUID) -> Result[GenerationJob]:
        """Find a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Result containing the job or NotFoundError
        """
        pass

    @abstractmethod
    async def find_by_session(
        self,
        session_id: UUID,
        status: Optional[GenerationStatus] = None,
        kind: Optional[GenerationKind] = None,
        limit: int = 50
    ) -> Result[list[GenerationJob]]:
        """Find jobs for a session.

        Args:
            session_id: Session identifier
            status: Optional status filter
            kind: Optional kind filter
            limit: Maximum results to return

        Returns:
            Result containing list of jobs
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        job_id: UUID,
        new_status: GenerationStatus,
        error: Optional[str] = None
    ) -> Result[GenerationJob]:
        """Update job status.

        Args:
            job_id: Job identifier
            new_status: New status
            error: Optional error message for failed status

        Returns:
            Result containing updated job
        """
        pass

    @abstractmethod
    async def delete(self, job_id: UUID) -> Result[None]:
        """Delete a job.

        Args:
            job_id: Job identifier

        Returns:
            Result indicating success or failure
        """
        pass


class GeneratedDesignRepositoryPort(ABC):
    """Repository port for GeneratedDesign entities."""

    @abstractmethod
    async def save(self, design: GeneratedDesign) -> Result[GeneratedDesign]:
        """Save a generated design.

        Args:
            design: The design to save

        Returns:
            Result containing the saved design
        """
        pass

    @abstractmethod
    async def find_by_id(self, design_id: UUID) -> Result[GeneratedDesign]:
        """Find a design by ID.

        Args:
            design_id: Design identifier

        Returns:
            Result containing the design or NotFoundError
        """
        pass

    @abstractmethod
    async def find_by_job(self, job_id: UUID) -> Result[list[GeneratedDesign]]:
        """Find all designs for a job.

        Args:
            job_id: Job identifier

        Returns:
            Result containing list of designs
        """
        pass

    @abstractmethod
    async def find_by_session(
        self,
        session_id: UUID,
        limit: int = 50
    ) -> Result[list[GeneratedDesign]]:
        """Find designs for a session.

        Args:
            session_id: Session identifier
            limit: Maximum results to return

        Returns:
            Result containing list of designs
        """
        pass


class ModelRouterPort(ABC):
    """Port for SPEC-04 ModelRouter integration.

    REQ-03-GEN-006: All model calls go through SPEC-04 ModelRouter
    """

    @abstractmethod
    async def generate_image(
        self,
        model_key: str,
        prompt: str,
        policy_key: str,
        size: str = "1024x1024",
        n: int = 1
    ) -> Result:
        """Generate an image using the specified model.

        Args:
            model_key: Model identifier (e.g., "seedream-4.5")
            prompt: Generation prompt
            policy_key: Model routing policy key
            size: Image size (e.g., "1024x1024")
            n: Number of images to generate

        Returns:
            Result containing asset_uri and cost_metadata
        """
        pass


class ObjectStoragePort(ABC):
    """Port for object storage operations.

    This is a shared port from shared.infrastructure.
    """

    @abstractmethod
    async def upload_bytes(
        self,
        data: bytes,
        path: str,
        content_type: str
    ) -> Result[str]:
        """Upload bytes to object storage.

        Args:
            data: Bytes to upload
            path: Storage path/key
            content_type: MIME type

        Returns:
            Result containing the URI of the uploaded object
        """
        pass

    @abstractmethod
    async def get_url(self, path: str, expires_in: int = 3600) -> Result[str]:
        """Get a presigned URL for an object.

        Args:
            path: Storage path/key
            expires_in: URL expiration time in seconds

        Returns:
            Result containing the presigned URL
        """
        pass


class AbstractionRulePort(ABC):
    """Port for reading abstraction rules.

    Used by variation jobs to apply rules.
    """

    @abstractmethod
    async def find_by_ids(self, rule_ids: list[UUID]) -> Result[list]:
        """Find rules by IDs.

        Args:
            rule_ids: List of rule identifiers

        Returns:
            Result containing list of rules
        """
        pass


class ConceptPort(ABC):
    """Port for reading concepts.

    Used to fetch concept details for generation.
    """

    @abstractmethod
    async def find_by_id(self, concept_id: UUID) -> Result:
        """Find a concept by ID.

        Args:
            concept_id: Concept identifier

        Returns:
            Result containing the concept
        """
        pass


class SketchAnalysisPort(ABC):
    """Port for reading sketch analysis from SPEC-01.

    Used by refinement jobs to access parent sketches.
    """

    @abstractmethod
    async def find_by_id(self, sketch_id: UUID) -> Result:
        """Find a sketch by ID.

        Args:
            sketch_id: Sketch identifier

        Returns:
            Result containing the sketch
        """
        pass
