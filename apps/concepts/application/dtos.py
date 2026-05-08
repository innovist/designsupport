"""Data Transfer Objects for concepts module."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ConceptCandidateDTO:
    """DTO for concept candidate."""
    id: UUID
    session_id: UUID
    title: str
    description: str
    rationale: str
    rationale_refs: list[UUID]
    domain_tags: list[str]
    status: str
    score: Optional[float]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, concept) -> 'ConceptCandidateDTO':
        """Create DTO from domain entity."""
        return cls(
            id=concept.id,
            session_id=concept.session_id,
            title=concept.title,
            description=concept.description,
            rationale=concept.rationale,
            rationale_refs=concept.rationale_refs,
            domain_tags=concept.domain_tags,
            status=concept.status.value,
            score=concept.score,
            created_by=concept.created_by,
            created_at=concept.created_at,
            updated_at=concept.updated_at,
        )


@dataclass
class ConceptDecisionDTO:
    """DTO for concept decision."""
    id: UUID
    concept_id: UUID
    decision: str
    actor_kind: str
    actor_id: UUID
    rationale: str
    created_at: datetime

    @classmethod
    def from_entity(cls, decision) -> 'ConceptDecisionDTO':
        """Create DTO from domain entity."""
        return cls(
            id=decision.id,
            concept_id=decision.concept_id,
            decision=decision.decision.value,
            actor_kind=decision.actor_kind.value,
            actor_id=decision.actor_id,
            rationale=decision.rationale,
            created_at=decision.created_at,
        )


@dataclass
class ProposeConceptRequest:
    """Request DTO for proposing a concept."""
    session_id: UUID
    title: str
    description: str
    rationale: str
    rationale_refs: list[UUID]
    domain_tags: list[str]
    created_by: UUID


@dataclass
class DecideConceptRequest:
    """Request DTO for deciding on a concept."""
    concept_id: UUID
    decision: str
    actor_kind: str
    actor_id: UUID
    rationale: str


@dataclass
class GenerateConceptsRequest:
    """Request DTO for generating multiple concepts.

    REQ-03-CONCEPT-001: Generate 3-5 concept candidates
    """
    session_id: UUID
    created_by: UUID
    count: int = 3  # Default to 3, max 5

    def __post_init__(self):
        """Validate request."""
        if self.count < 3 or self.count > 5:
            raise ValueError("Count must be between 3 and 5")
