"""Repositories for specs module."""
from apps.specs.infrastructure.repositories.spec_repository import (
    DjangoDomainPackRepository,
    DjangoSpecDocumentRepository,
)

__all__ = ["DjangoSpecDocumentRepository", "DjangoDomainPackRepository"]
