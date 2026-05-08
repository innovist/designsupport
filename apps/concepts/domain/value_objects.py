"""Value objects for concepts module.

This file is pure Python - no Django imports allowed.
"""
from dataclasses import dataclass

from shared.domain.exceptions import ValidationError


class ConceptStatusVO:
    """Value object for concept status with transition rules."""

    def __init__(self, status: str):
        valid_statuses = {"draft", "proposed", "adopted", "discarded"}
        if status not in valid_statuses:
            raise ValidationError(
                "status",
                f"Invalid status: {status}. Must be one of {valid_statuses}"
            )
        self._status = status

    @property
    def value(self) -> str:
        return self._status

    def can_transition_to(self, target: 'ConceptStatusVO') -> bool:
        """Check if transition is valid."""
        transitions = {
            "draft": ["proposed"],
            "proposed": ["adopted", "discarded"],
            "adopted": ["discarded"],
            "discarded": [],
        }
        return target.value in transitions.get(self._status, [])

    def __eq__(self, other) -> bool:
        if not isinstance(other, ConceptStatusVO):
            return False
        return self._status == other._status

    def __hash__(self) -> int:
        return hash(self._status)


class DecisionTypeVO:
    """Value object for decision type."""

    def __init__(self, decision: str):
        valid_decisions = {"adopt", "hold", "discard", "explore_more"}
        if decision not in valid_decisions:
            raise ValidationError(
                "decision",
                f"Invalid decision: {decision}. Must be one of {valid_decisions}"
            )
        self._decision = decision

    @property
    def value(self) -> str:
        return self._decision

    def __eq__(self, other) -> bool:
        if not isinstance(other, DecisionTypeVO):
            return False
        return self._decision == other._decision

    def __hash__(self) -> int:
        return hash(self._decision)


@dataclass
class ConceptScore:
    """Value object for concept scoring."""
    fit_score: float  # How well it fits the brief (0.0-1.0)
    novelty: float  # How novel/innovative it is (0.0-1.0)
    feasibility: float  # How feasible to implement (0.0-1.0)
    overall: float  # Weighted overall score (0.0-1.0)

    def __post_init__(self):
        """Validate score ranges."""
        for field_name in ["fit_score", "novelty", "feasibility", "overall"]:
            value = getattr(self, field_name)
            if value < 0.0 or value > 1.0:
                raise ValidationError(
                    field_name,
                    f"{field_name} must be between 0.0 and 1.0, got {value}"
                )

    @classmethod
    def calculate(cls, fit_score: float, novelty: float, feasibility: float) -> 'ConceptScore':
        """Calculate overall score with default weights."""
        # Default weights: fit=0.4, novelty=0.3, feasibility=0.3
        overall = (fit_score * 0.4) + (novelty * 0.3) + (feasibility * 0.3)
        return cls(
            fit_score=fit_score,
            novelty=novelty,
            feasibility=feasibility,
            overall=overall
        )
