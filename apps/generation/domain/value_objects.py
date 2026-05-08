"""Value objects for generation module.

This file is pure Python - no Django imports allowed.
"""
from enum import Enum


class GenerationStatus(str, Enum):
    """Status of a generation job.

    Lifecycle:
        queued -> running -> completed
                      -> failed
                      -> cancelled

    Terminal states: completed, failed, cancelled
    """
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def can_transition_to(self, target: 'GenerationStatus') -> bool:
        """Check if state transition is valid."""
        transitions = {
            GenerationStatus.QUEUED: [
                GenerationStatus.RUNNING,
                GenerationStatus.FAILED,
                GenerationStatus.CANCELLED
            ],
            GenerationStatus.RUNNING: [
                GenerationStatus.COMPLETED,
                GenerationStatus.FAILED,
                GenerationStatus.CANCELLED
            ],
            GenerationStatus.COMPLETED: [],  # Terminal state
            GenerationStatus.FAILED: [GenerationStatus.QUEUED],  # Can retry
            GenerationStatus.CANCELLED: [],  # Terminal state
        }
        return target in transitions.get(self, [])

    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in {
            GenerationStatus.COMPLETED,
            GenerationStatus.FAILED,
            GenerationStatus.CANCELLED
        }

    def is_active(self) -> bool:
        """Check if job is still active (not terminal)."""
        return not self.is_terminal()


class GenerationKind(str, Enum):
    """Type of generation job.

    sketch: Initial design sketch from brief/concept
    refinement: Refine existing UserSketchAsset with new prompts
    variation: Create variations applying abstraction rules
    domain_application: Apply design to specific domain pack format
    """
    SKETCH = "sketch"
    REFINEMENT = "refinement"
    VARIATION = "variation"
    DOMAIN_APPLICATION = "domain_application"

    def requires_parent_sketch(self) -> bool:
        """Check if this kind requires a parent sketch."""
        return self == GenerationKind.REFINEMENT

    def requires_rules(self) -> bool:
        """Check if this kind requires abstraction rules."""
        return self == GenerationKind.VARIATION

    def requires_domain_pack(self) -> bool:
        """Check if this kind requires domain pack configuration."""
        return self == GenerationKind.DOMAIN_APPLICATION


class AssetKind(str, Enum):
    """Types of generated design assets."""
    IMAGE = "image"
    THUMBNAIL = "thumbnail"
    ANNOTATED = "annotated"
    COMPOSITE = "composite"
