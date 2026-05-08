"""Django ORM models for concepts module."""
from django.db import models

from shared.infrastructure.orm.base_model import TimestampedModel


class ConceptCandidateModel(TimestampedModel):
    """Django model for ConceptCandidate entity."""

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField()
    rationale = models.TextField()
    rationale_refs = models.JSONField(default=list)  # List of UUIDs
    risks = models.JSONField(default=list)  # List of risk strings
    domain_tags = models.JSONField(default=list)
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("proposed", "Proposed"),
            ("adopted", "Adopted"),
            ("discarded", "Discarded"),
        ],
        default="draft",
    )
    score = models.FloatField(null=True, blank=True)
    novelty = models.FloatField(null=True, blank=True)
    fit_score = models.FloatField(null=True, blank=True)
    created_by = models.UUIDField()

    class Meta:
        db_table = "concept_candidates"
        indexes = [
            models.Index(fields=["session_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.concepts.domain.entities import ConceptCandidate, ConceptStatus
        from uuid import UUID

        return ConceptCandidate(
            id=UUID(str(self.id)),
            session_id=UUID(str(self.session_id)),
            title=self.title,
            description=self.description,
            rationale=self.rationale,
            rationale_refs=[UUID(str(ref)) for ref in self.rationale_refs],
            risks=self.risks,
            domain_tags=self.domain_tags,
            status=ConceptStatus(self.status),
            score=self.score,
            novelty=self.novelty,
            fit_score=self.fit_score,
            created_by=UUID(str(self.created_by)),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, concept):
        """Create ORM model from domain entity."""
        return cls(
            id=str(concept.id),
            session_id=str(concept.session_id),
            title=concept.title,
            description=concept.description,
            rationale=concept.rationale,
            rationale_refs=[str(ref) for ref in concept.rationale_refs],
            risks=concept.risks,
            domain_tags=concept.domain_tags,
            status=concept.status.value,
            score=concept.score,
            novelty=concept.novelty,
            fit_score=concept.fit_score,
            created_by=str(concept.created_by),
            created_at=concept.created_at,
            updated_at=concept.updated_at,
        )


class ConceptDecisionModel(TimestampedModel):
    """Django model for ConceptDecision entity."""

    id = models.UUIDField(primary_key=True)
    concept_id = models.UUIDField(db_index=True)
    decision = models.CharField(
        max_length=20,
        choices=[
            ("adopt", "Adopt"),
            ("hold", "Hold"),
            ("discard", "Discard"),
            ("explore_more", "Explore More"),
        ],
    )
    actor_kind = models.CharField(
        max_length=10,
        choices=[
            ("user", "User"),
            ("auto", "Auto"),
        ],
    )
    actor_id = models.UUIDField()
    rationale = models.TextField()
    evidence_refs = models.JSONField(default=list)  # List of UUIDs

    class Meta:
        db_table = "concept_decisions"
        indexes = [
            models.Index(fields=["concept_id"]),
            models.Index(fields=["created_at"]),
        ]

    def to_domain(self):
        """Convert ORM model to domain entity."""
        from apps.concepts.domain.entities import ConceptDecision, DecisionType, ActorKind
        from uuid import UUID

        return ConceptDecision(
            id=UUID(str(self.id)),
            concept_id=UUID(str(self.concept_id)),
            decision=DecisionType(self.decision),
            actor_kind=ActorKind(self.actor_kind),
            actor_id=UUID(str(self.actor_id)),
            rationale=self.rationale,
            evidence_refs=[UUID(str(ref)) for ref in self.evidence_refs],
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, decision):
        """Create ORM model from domain entity."""
        return cls(
            id=str(decision.id),
            concept_id=str(decision.concept_id),
            decision=decision.decision.value,
            actor_kind=decision.actor_kind.value,
            actor_id=str(decision.actor_id),
            rationale=decision.rationale,
            evidence_refs=[str(ref) for ref in decision.evidence_refs],
            created_at=decision.created_at,
        )
