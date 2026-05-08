"""Application layer for specs module.

This module contains use cases, ports, and DTOs.
"""
from apps.specs.application.dtos import (
    ApproveSpecRequest,
    CreateSpecRequest,
    DomainPackDTO,
    RejectSpecRequest,
    SpecDocumentDTO,
    SpecSectionDTO,
    SubmitForReviewRequest,
    UpdateSectionRequest,
    VersionDiffDTO,
)
from apps.specs.application.ports import (
    AbstractionRulePort,
    ConceptPort,
    DomainPackRepositoryPort,
    GenerationJobPort,
    SessionPort,
    SpecDocumentRepositoryPort,
)

__all__ = [
    # DTOs
    "SpecDocumentDTO",
    "DomainPackDTO",
    "SpecSectionDTO",
    "VersionDiffDTO",
    "CreateSpecRequest",
    "SubmitForReviewRequest",
    "ApproveSpecRequest",
    "RejectSpecRequest",
    "UpdateSectionRequest",
    # Ports
    "SpecDocumentRepositoryPort",
    "DomainPackRepositoryPort",
    "ConceptPort",
    "AbstractionRulePort",
    "GenerationJobPort",
    "SessionPort",
]
