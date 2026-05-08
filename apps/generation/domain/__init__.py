"""Domain layer for generation module.

This module contains pure Python domain logic with no Django dependencies.
"""

from apps.generation.domain.entities import (
    GenerationJob,
    GeneratedDesign,
    CostMetadata
)

from apps.generation.domain.value_objects import (
    GenerationStatus,
    GenerationKind,
    AssetKind
)

from apps.generation.domain.services import (
    GenerationJobValidator,
    FallbackChainExecutor,
    CostCalculator
)

__all__ = [
    # Entities
    "GenerationJob",
    "GeneratedDesign",
    "CostMetadata",

    # Value Objects
    "GenerationStatus",
    "GenerationKind",
    "AssetKind",

    # Services
    "GenerationJobValidator",
    "FallbackChainExecutor",
    "CostCalculator",
]
