"""Design session value objects.

State machine and status value objects for SPEC-01 §5.3.
"""
from enum import Enum
from typing import Dict, Set, Tuple


class SessionStatus(Enum):
    """Session status enum.

    Transition rules are defined in SESSION_TRANSITIONS (module-level).
    """

    QUEUED = "queued"
    RESEARCHING = "researching"
    CONCEPTING = "concepting"
    REFERENCING = "referencing"
    ABSTRACTING = "abstracting"
    GENERATING = "generating"
    DOCUMENTING = "documenting"
    REVIEW_READY = "review_ready"
    FAILED = "failed"

    def can_transition_to(self, target: "SessionStatus") -> bool:
        return target in SESSION_TRANSITIONS[self]

    def get_allowed_transitions(self) -> Set["SessionStatus"]:
        return SESSION_TRANSITIONS[self].copy()

    def is_terminal(self) -> bool:
        return len(SESSION_TRANSITIONS[self]) == 0


# Module-level transition table (SPEC-01 §5.3 state machine)
SESSION_TRANSITIONS: Dict[SessionStatus, Set[SessionStatus]] = {
    SessionStatus.QUEUED: {SessionStatus.RESEARCHING, SessionStatus.FAILED},
    SessionStatus.RESEARCHING: {SessionStatus.CONCEPTING, SessionStatus.FAILED},
    SessionStatus.CONCEPTING: {SessionStatus.REFERENCING, SessionStatus.FAILED},
    SessionStatus.REFERENCING: {SessionStatus.ABSTRACTING, SessionStatus.FAILED},
    SessionStatus.ABSTRACTING: {SessionStatus.GENERATING, SessionStatus.FAILED},
    SessionStatus.GENERATING: {SessionStatus.DOCUMENTING, SessionStatus.FAILED},
    SessionStatus.DOCUMENTING: {SessionStatus.REVIEW_READY, SessionStatus.FAILED},
    SessionStatus.REVIEW_READY: set(),
    SessionStatus.FAILED: {
        SessionStatus.QUEUED, SessionStatus.RESEARCHING,
        SessionStatus.CONCEPTING, SessionStatus.REFERENCING,
        SessionStatus.ABSTRACTING, SessionStatus.GENERATING,
    },
}


class SessionMode(Enum):
    """Session execution mode."""

    GUIDED = "guided"
    AUTO = "auto"

    def is_automatic(self) -> bool:
        return self == SessionMode.AUTO


class PipelineStep(Enum):
    """17-step pipeline stages (SPEC-01 §5.4)."""

    PURPOSE_INPUT = 1
    BRIEF_STRUCTURE = 2
    SKETCH_UPLOAD = 3
    CLARIFYING_QUESTIONS = 4
    TREND_RESEARCH = 5
    CONCEPT_GENERATION = 6
    CONCEPT_EVALUATION = 7
    CONCEPT_DECISION = 8
    REFERENCE_SEARCH = 9
    REFERENCE_CLUSTERING = 10
    SKETCH_ANALYSIS = 11
    ABSTRACTION = 12
    GENERATION = 13
    DOMAIN_APPLICATION = 14
    COMPARISON = 15
    SPEC_DOCUMENT = 16
    REVIEW = 17

    def get_session_status(self) -> SessionStatus:
        return STEP_STATUS_MAPPING[self]

    def get_step_range(self) -> Tuple[int, int]:
        status = self.get_session_status()
        steps = [s for s, s_st in STEP_STATUS_MAPPING.items() if s_st == status]
        return (min(steps, key=lambda s: s.value).value,
                max(steps, key=lambda s: s.value).value)


# Module-level step-to-status mapping (SPEC-01 §5.4)
STEP_STATUS_MAPPING: Dict[PipelineStep, SessionStatus] = {
    PipelineStep.PURPOSE_INPUT: SessionStatus.QUEUED,
    PipelineStep.BRIEF_STRUCTURE: SessionStatus.QUEUED,
    PipelineStep.SKETCH_UPLOAD: SessionStatus.QUEUED,
    PipelineStep.CLARIFYING_QUESTIONS: SessionStatus.QUEUED,
    PipelineStep.TREND_RESEARCH: SessionStatus.RESEARCHING,
    PipelineStep.CONCEPT_GENERATION: SessionStatus.CONCEPTING,
    PipelineStep.CONCEPT_EVALUATION: SessionStatus.CONCEPTING,
    PipelineStep.CONCEPT_DECISION: SessionStatus.CONCEPTING,
    PipelineStep.REFERENCE_SEARCH: SessionStatus.REFERENCING,
    PipelineStep.REFERENCE_CLUSTERING: SessionStatus.REFERENCING,
    PipelineStep.SKETCH_ANALYSIS: SessionStatus.ABSTRACTING,
    PipelineStep.ABSTRACTION: SessionStatus.ABSTRACTING,
    PipelineStep.GENERATION: SessionStatus.GENERATING,
    PipelineStep.DOMAIN_APPLICATION: SessionStatus.GENERATING,
    PipelineStep.COMPARISON: SessionStatus.GENERATING,
    PipelineStep.SPEC_DOCUMENT: SessionStatus.DOCUMENTING,
    PipelineStep.REVIEW: SessionStatus.REVIEW_READY,
}
