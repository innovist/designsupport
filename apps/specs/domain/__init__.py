"""Domain layer for specs module.

This module contains pure Python domain entities and value objects.
No Django imports are allowed in this layer.
"""
from apps.specs.domain.entities import REQUIRED_SECTION_TYPES, DomainPack, SpecDocument
from apps.specs.domain.services import (
    DomainPackResolver,
    SpecDocumentValidator,
    SpecVersionManager,
)
from apps.specs.domain.value_objects import SpecSection, SpecStatus, VersionDiff

__all__ = [
    # Entities
    "SpecDocument",
    "DomainPack",
    "REQUIRED_SECTION_TYPES",
    # Value objects
    "SpecStatus",
    "SpecSection",
    "VersionDiff",
    # Services
    "SpecDocumentValidator",
    "SpecVersionManager",
    "DomainPackResolver",
]
