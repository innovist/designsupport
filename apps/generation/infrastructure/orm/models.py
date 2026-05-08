"""Django ORM models for generation module."""
from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError

from shared.infrastructure.orm.base_model import TimestampedModel


class GenerationJobModel(TimestampedModel):
    """Django model for GenerationJob entity."""

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    kind = models.CharField(
        max_length=30,
        choices=[
            ("sketch", "Sketch"),
            ("refinement", "Refinement"),
            ("variation", "Variation"),
            ("domain_application", "Domain Application"),
        ],
        db_index=True
    )
    prompt_id = models.UUIDField(null=True, blank=True, db_index=True)
    brief_id = models.UUIDField(null=True, blank=True, db_index=True)
    concept_id = models.UUIDField(null=True, blank=True, db_index=True)
    rule_ids = models.JSONField(default=list)  # List of UUIDs
    sketch_id = models.UUIDField(null=True, blank=True, db_index=True)
    reference_ids = models.JSONField(default=list)  # List of UUIDs
    status = models.CharField(
        max_length=20,
        choices=[
            ("queued", "Queued"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="queued",
        db_index=True
    )
    model_policy_key = models.CharField(max_length=100)
    retries = models.IntegerField(default=0)
    cost_meta = models.JSONField(null=True, blank=True)  # CostMetadata as dict
    error_message = models.TextField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "generation_jobs"
        indexes = [
            models.Index(fields=["session_id", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["kind", "-created_at"]),
        ]

    def clean(self):
        """Validate model before save."""
        # REQ-03-GEN-002: Must link to at least one context
        has_brief = self.brief_id is not None
        has_concept = self.concept_id is not None
        has_rules = len(self.rule_ids) > 0
        has_references = len(self.reference_ids) > 0

        if not (has_brief or has_concept or has_rules or has_references):
            raise DjangoValidationError(
                "Job must link to at least one of: brief, concept, rule, or reference"
            )

        # Kind-specific validation
        if self.kind == "refinement" and self.sketch_id is None:
            raise DjangoValidationError(
                "Refinement jobs require a parent sketch"
            )

        if self.kind == "variation" and len(self.rule_ids) == 0:
            raise DjangoValidationError(
                "Variation jobs require at least one abstraction rule"
            )

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.generation.domain.entities import GenerationJob, CostMetadata
        from apps.generation.domain.value_objects import GenerationStatus, GenerationKind
        from uuid import UUID
        from datetime import timezone

        cost_meta = None
        if self.cost_meta:
            cost_meta = CostMetadata(
                model_key=self.cost_meta["model_key"],
                prompt_tokens=self.cost_meta["prompt_tokens"],
                completion_tokens=self.cost_meta["completion_tokens"],
                total_tokens=self.cost_meta["total_tokens"],
                cost_usd=self.cost_meta["cost_usd"]
            )

        return GenerationJob(
            id=UUID(str(self.id)),
            session_id=UUID(str(self.session_id)),
            kind=GenerationKind(self.kind),
            prompt_id=UUID(str(self.prompt_id)) if self.prompt_id else None,
            brief_id=UUID(str(self.brief_id)) if self.brief_id else None,
            concept_id=UUID(str(self.concept_id)) if self.concept_id else None,
            rule_ids=[UUID(str(rid)) for rid in self.rule_ids],
            sketch_id=UUID(str(self.sketch_id)) if self.sketch_id else None,
            reference_ids=[UUID(str(rid)) for rid in self.reference_ids],
            status=GenerationStatus(self.status),
            model_policy_key=self.model_policy_key,
            retries=self.retries,
            cost_meta=cost_meta,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at,
            completed_at=self.completed_at
        )

    @classmethod
    def from_domain(cls, job):
        """Create ORM model from domain entity."""
        cost_meta = None
        if job.cost_meta:
            cost_meta = {
                "model_key": job.cost_meta.model_key,
                "prompt_tokens": job.cost_meta.prompt_tokens,
                "completion_tokens": job.cost_meta.completion_tokens,
                "total_tokens": job.cost_meta.total_tokens,
                "cost_usd": job.cost_meta.cost_usd
            }

        return cls(
            id=str(job.id),
            session_id=str(job.session_id),
            kind=job.kind.value,
            prompt_id=str(job.prompt_id) if job.prompt_id else None,
            brief_id=str(job.brief_id) if job.brief_id else None,
            concept_id=str(job.concept_id) if job.concept_id else None,
            rule_ids=[str(rid) for rid in job.rule_ids],
            sketch_id=str(job.sketch_id) if job.sketch_id else None,
            reference_ids=[str(rid) for rid in job.reference_ids],
            status=job.status.value,
            model_policy_key=job.model_policy_key,
            retries=job.retries,
            cost_meta=cost_meta,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at
        )


class GeneratedDesignModel(TimestampedModel):
    """Django model for GeneratedDesign entity."""

    id = models.UUIDField(primary_key=True)
    job_id = models.UUIDField(db_index=True)
    asset_uri = models.TextField()  # Can be long URL
    asset_kind = models.CharField(
        max_length=20,
        choices=[
            ("image", "Image"),
            ("thumbnail", "Thumbnail"),
            ("annotated", "Annotated"),
            ("composite", "Composite"),
        ],
        default="image"
    )
    parent_sketch_id = models.UUIDField(null=True, blank=True, db_index=True)
    brief_id = models.UUIDField(null=True, blank=True, db_index=True)
    concept_id = models.UUIDField(null=True, blank=True, db_index=True)
    rule_ids = models.JSONField(default=list)  # List of UUIDs
    reference_ids = models.JSONField(default=list)  # List of UUIDs
    model_policy_key = models.CharField(max_length=100)
    prompt_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "generated_designs"
        indexes = [
            models.Index(fields=["job_id"]),
            models.Index(fields=["created_at"]),
        ]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.generation.domain.entities import GeneratedDesign
        from apps.generation.domain.value_objects import AssetKind
        from uuid import UUID

        return GeneratedDesign(
            id=UUID(str(self.id)),
            job_id=UUID(str(self.job_id)),
            asset_uri=self.asset_uri,
            asset_kind=AssetKind(self.asset_kind),
            parent_sketch_id=UUID(str(self.parent_sketch_id)) if self.parent_sketch_id else None,
            brief_id=UUID(str(self.brief_id)) if self.brief_id else None,
            concept_id=UUID(str(self.concept_id)) if self.concept_id else None,
            rule_ids=[UUID(str(rid)) for rid in self.rule_ids],
            reference_ids=[UUID(str(rid)) for rid in self.reference_ids],
            model_policy_key=self.model_policy_key,
            prompt_id=UUID(str(self.prompt_id)) if self.prompt_id else None,
            created_at=self.created_at
        )

    @classmethod
    def from_domain(cls, design):
        """Create ORM model from domain entity."""
        return cls(
            id=str(design.id),
            job_id=str(design.job_id),
            asset_uri=design.asset_uri,
            asset_kind=design.asset_kind.value,
            parent_sketch_id=str(design.parent_sketch_id) if design.parent_sketch_id else None,
            brief_id=str(design.brief_id) if design.brief_id else None,
            concept_id=str(design.concept_id) if design.concept_id else None,
            rule_ids=[str(rid) for rid in design.rule_ids],
            reference_ids=[str(rid) for rid in design.reference_ids],
            model_policy_key=design.model_policy_key,
            prompt_id=str(design.prompt_id) if design.prompt_id else None,
            created_at=design.created_at
        )
