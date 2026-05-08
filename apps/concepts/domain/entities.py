"""Domain entities for concepts module.

This file is pure Python - no Django imports allowed.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from shared.domain.exceptions import ValidationError


class ConceptStatus(str, Enum):
    """Status of a concept candidate."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    ADOPTED = "adopted"
    DISCARDED = "discarded"

    def can_transition_to(self, target: 'ConceptStatus') -> bool:
        """Check if state transition is valid."""
        transitions = {
            ConceptStatus.DRAFT: [ConceptStatus.PROPOSED],
            ConceptStatus.PROPOSED: [ConceptStatus.ADOPTED, ConceptStatus.DISCARDED],
            ConceptStatus.ADOPTED: [ConceptStatus.DISCARDED],  # Undo adoption
            ConceptStatus.DISCARDED: [],  # Terminal state
        }
        return target in transitions.get(self, [])


class DecisionType(str, Enum):
    """Types of concept decisions."""
    ADOPT = "adopt"
    HOLD = "hold"
    DISCARD = "discard"
    EXPLORE_MORE = "explore_more"


class ActorKind(str, Enum):
    """Who made the decision."""
    USER = "user"
    AUTO = "auto"


@dataclass
class ConceptCandidate:
    """A concept candidate for design exploration.

    Attributes:
        id: Unique identifier
        session_id: Associated design session
        title: Concept title
        description: Detailed description
        rationale: Reasoning behind this concept
        rationale_refs: References to TrendInsight or ReferenceAnalysis (min 1 required)
        domain_tags: Domain-specific tags
        status: Current status
        score: Automated scoring result
        novelty: Novelty score (0.0-1.0)
        fit_score: Fit to brief score (0.0-1.0)
        created_by: User who created the concept
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    id: UUID = field(default_factory=uuid4)
    session_id: UUID = field(kw_only=True)
    title: str = field(kw_only=True)
    description: str = field(kw_only=True)
    rationale: str = field(kw_only=True)
    rationale_refs: list[UUID] = field(kw_only=True)
    risks: list[str] = field(default_factory=list)
    domain_tags: list[str] = field(default_factory=list)
    status: ConceptStatus = field(default=ConceptStatus.DRAFT, kw_only=True)
    score: Optional[float] = field(default=None, kw_only=True)
    novelty: Optional[float] = field(default=None, kw_only=True)
    fit_score: Optional[float] = field(default=None, kw_only=True)
    created_by: UUID = field(kw_only=True)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate concept candidate."""
        if not self.title or not self.title.strip():
            raise ValidationError("title", "Title cannot be empty")
        if not self.description or not self.description.strip():
            raise ValidationError("description", "Description cannot be empty")
        if not self.rationale or not self.rationale.strip():
            raise ValidationError("rationale", "Rationale cannot be empty")
        if len(self.rationale_refs) == 0:
            raise ValidationError(
                "rationale_refs",
                "At least one rationale reference (TrendInsight or ReferenceAnalysis) is required"
            )
        if self.score is not None and (self.score < 0.0 or self.score > 1.0):
            raise ValidationError("score", "Score must be between 0.0 and 1.0")
        if self.novelty is not None and (self.novelty < 0.0 or self.novelty > 1.0):
            raise ValidationError("novelty", "Novelty must be between 0.0 and 1.0")
        if self.fit_score is not None and (self.fit_score < 0.0 or self.fit_score > 1.0):
            raise ValidationError("fit_score", "Fit score must be between 0.0 and 1.0")

    def transition_to(self, new_status: ConceptStatus) -> None:
        """Transition to a new status if valid."""
        if not self.status.can_transition_to(new_status):
            raise ValidationError(
                "status",
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def update_score(self, new_score: float) -> None:
        """Update the concept score."""
        if new_score < 0.0 or new_score > 1.0:
            raise ValidationError("score", "Score must be between 0.0 and 1.0")
        self.score = new_score
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ConceptDecision:
    """Decision record for a concept candidate.

    Attributes:
        id: Unique identifier
        concept_id: Associated concept candidate
        decision: Type of decision
        actor_kind: User or auto decision
        actor_id: User or system ID
        rationale: Reasoning for the decision
        evidence_refs: References to supporting evidence
        created_at: Decision timestamp
    """
    id: UUID = field(default_factory=uuid4)
    concept_id: UUID = field(kw_only=True)
    decision: DecisionType = field(kw_only=True)
    actor_kind: ActorKind = field(kw_only=True)
    actor_id: UUID = field(kw_only=True)
    rationale: str = field(kw_only=True)
    evidence_refs: list[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate decision."""
        if not self.rationale or not self.rationale.strip():
            raise ValidationError("rationale", "Decision rationale cannot be empty")
