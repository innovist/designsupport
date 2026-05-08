"""Repository implementation for GenerationJob."""
from typing import Optional

from apps.generation.application.ports import GenerationJobRepositoryPort
from apps.generation.domain.entities import GenerationJob
from apps.generation.domain.value_objects import GenerationStatus, GenerationKind
from apps.generation.infrastructure.orm.models import GenerationJobModel
from shared.application.result import Result
from shared.domain.exceptions import NotFoundError


# @MX:ANCHOR: [AUTO] GenerationJob persistence with status tracking
# @MX:REASON: Job lifecycle management; used by async tasks and job listing workflows
class DjangoGenerationJobRepository(GenerationJobRepositoryPort):
    """Django ORM implementation of GenerationJob repository."""

    async def save(self, job: GenerationJob) -> Result[GenerationJob]:
        """Save a generation job.

        Args:
            job: The job to save

        Returns:
            Result containing the saved job
        """
        try:
            orm_job = GenerationJobModel.from_domain(job)
            orm_job.full_clean()
            orm_job.save()

            # Convert back to domain
            saved_job = orm_job.to_domain()
            return Result.success(saved_job)

        except Exception as e:
            return Result.failure(e)

    async def find_by_id(self, job_id) -> Result[GenerationJob]:
        """Find a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Result containing the job or NotFoundError
        """
        try:
            orm_job = await GenerationJobModel.objects.aget(id=str(job_id))
            job = orm_job.to_domain()
            return Result.success(job)

        except GenerationJobModel.DoesNotExist:
            return Result.failure(NotFoundError("GenerationJob", str(job_id)))

        except Exception as e:
            return Result.failure(e)

    async def find_by_session(
        self,
        session_id,
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
        try:
            queryset = GenerationJobModel.objects.filter(
                session_id=str(session_id)
            )

            if status:
                queryset = queryset.filter(status=status.value)

            if kind:
                queryset = queryset.filter(kind=kind.value)

            orm_jobs = [
                job async for job in queryset.order_by('-created_at')[:limit]
            ]

            jobs = [job.to_domain() for job in orm_jobs]
            return Result.success(jobs)

        except Exception as e:
            return Result.failure(e)

    async def update_status(
        self,
        job_id,
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
        try:
            orm_job = await GenerationJobModel.objects.aget(id=str(job_id))

            # Update status
            orm_job.status = new_status.value

            if new_status.is_terminal():
                from django.utils import timezone
                orm_job.completed_at = timezone.now()

            if error and new_status == GenerationStatus.FAILED:
                orm_job.error_message = error

            orm_job.save()

            job = orm_job.to_domain()
            return Result.success(job)

        except GenerationJobModel.DoesNotExist:
            return Result.failure(NotFoundError("GenerationJob", str(job_id)))

        except Exception as e:
            return Result.failure(e)

    async def delete(self, job_id) -> Result[None]:
        """Delete a job.

        Args:
            job_id: Job identifier

        Returns:
            Result indicating success or failure
        """
        try:
            orm_job = await GenerationJobModel.objects.aget(id=str(job_id))
            await orm_job.adelete()
            return Result.success(None)

        except GenerationJobModel.DoesNotExist:
            return Result.failure(NotFoundError("GenerationJob", str(job_id)))

        except Exception as e:
            return Result.failure(e)
