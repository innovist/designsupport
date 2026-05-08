"""Repository implementation for GeneratedDesign."""
from typing import Optional

from apps.generation.application.ports import GeneratedDesignRepositoryPort
from apps.generation.domain.entities import GeneratedDesign
from apps.generation.infrastructure.orm.models import GeneratedDesignModel
from shared.application.result import Result
from shared.domain.exceptions import NotFoundError


class DjangoGeneratedDesignRepository(GeneratedDesignRepositoryPort):
    """Django ORM implementation of GeneratedDesign repository."""

    async def save(self, design: GeneratedDesign) -> Result[GeneratedDesign]:
        """Save a generated design.

        Args:
            design: The design to save

        Returns:
            Result containing the saved design
        """
        try:
            orm_design = GeneratedDesignModel.from_domain(design)
            orm_design.full_clean()
            orm_design.save()

            # Convert back to domain
            saved_design = orm_design.to_domain()
            return Result.success(saved_design)

        except Exception as e:
            return Result.failure(e)

    async def find_by_id(self, design_id) -> Result[GeneratedDesign]:
        """Find a design by ID.

        Args:
            design_id: Design identifier

        Returns:
            Result containing the design or NotFoundError
        """
        try:
            orm_design = await GeneratedDesignModel.objects.aget(id=str(design_id))
            design = orm_design.to_domain()
            return Result.success(design)

        except GeneratedDesignModel.DoesNotExist:
            return Result.failure(NotFoundError("GeneratedDesign", str(design_id)))

        except Exception as e:
            return Result.failure(e)

    async def find_by_job(self, job_id) -> Result[list[GeneratedDesign]]:
        """Find all designs for a job.

        Args:
            job_id: Job identifier

        Returns:
            Result containing list of designs
        """
        try:
            orm_designs = [
                design async for design in
                GeneratedDesignModel.objects.filter(job_id=str(job_id))
            ]

            designs = [design.to_domain() for design in orm_designs]
            return Result.success(designs)

        except Exception as e:
            return Result.failure(e)

    async def find_by_session(
        self,
        session_id,
        limit: int = 50
    ) -> Result[list[GeneratedDesign]]:
        """Find designs for a session.

        Args:
            session_id: Session identifier
            limit: Maximum results to return

        Returns:
            Result containing list of designs
        """
        try:
            # Join with GenerationJob to filter by session
            orm_designs = [
                design async for design in
                GeneratedDesignModel.objects.filter(
                    job_id__session_id=str(session_id)
                ).order_by('-created_at')[:limit]
            ]

            designs = [design.to_domain() for design in orm_designs]
            return Result.success(designs)

        except Exception as e:
            return Result.failure(e)
