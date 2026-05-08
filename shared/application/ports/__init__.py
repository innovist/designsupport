"""Application ports for external dependencies."""
from shared.application.ports.ports import (
    AuditLogPort,
    NotificationPort,
    ObjectStoragePort,
    SearchPort,
)


class RepositoryPort:
    """Minimal generic repository base for module-specific ports."""

    def __class_getitem__(cls, item):
        return cls


__all__ = [
    "AuditLogPort",
    "NotificationPort",
    "ObjectStoragePort",
    "RepositoryPort",
    "SearchPort",
]
