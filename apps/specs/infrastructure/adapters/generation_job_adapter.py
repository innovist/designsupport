"""Django ORM adapter for GenerationJob port.

Implements GenerationJobPort from generation module.
"""
from uuid import UUID

from apps.specs.application.ports import GenerationJobPort


class DjangoORMGenerationJobAdapter(GenerationJobPort):
    """Django ORM adapter for accessing generation jobs."""

    async def get_jobs_by_session(self, session_id: UUID) -> list[dict]:
        """Get all generation jobs for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of generation job data including design references
        """
        from apps.generation.infrastructure.orm.models import GenerationJobModel

        jobs = GenerationJobModel.objects.filter(session_id=str(session_id)).order_by("-created_at")
        return [
            {
                "id": str(job.id),
                "session_id": str(job.session_id),
                "kind": job.kind,
                "status": job.status,
                "prompt_id": str(job.prompt_id) if job.prompt_id else None,
                "brief_id": str(job.brief_id) if job.brief_id else None,
                "concept_id": str(job.concept_id) if job.concept_id else None,
                "rule_ids": job.rule_ids,
                "sketch_id": str(job.sketch_id) if job.sketch_id else None,
                "reference_ids": job.reference_ids,
                "model_policy_key": job.model_policy_key,
                "retries": job.retries,
                "error_message": job.error_message,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "created_at": job.created_at.isoformat(),
            }
            async for job in jobs
        ]

    async def get_designs_by_job(self, job_id: UUID) -> list[dict]:
        """Get all designs for a generation job.

        Args:
            job_id: Generation job UUID

        Returns:
            List of design data with full traceability metadata
        """
        from apps.generation.infrastructure.orm.models import GeneratedDesignModel

        designs = GeneratedDesignModel.objects.filter(job_id=str(job_id)).order_by("-created_at")
        return [
            {
                "id": str(design.id),
                "job_id": str(design.job_id),
                "status": design.status,
                "model_output_url": design.model_output_url,
                "thumbnail_url": design.thumbnail_url,
                "generation_metadata": design.generation_metadata,
                "trace_id": design.trace_id,
                "error_message": design.error_message,
                "created_at": design.created_at.isoformat(),
            }
            async for design in designs
        ]
