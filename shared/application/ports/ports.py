"""Port interfaces for external dependencies.

Ports define the contract between application logic and external services.
Implementations are provided in the infrastructure layer.
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class AuditLogPort(ABC):
    """Port for audit logging operations."""

    @abstractmethod
    async def log_action(
        self,
        actor_id: UUID,
        tenant_id: str,
        workspace_id: UUID,
        action_type: str,
        target_type: str,
        target_id: UUID | None,
        payload: dict[str, Any],
    ) -> None:
        """Log an audit action."""
        pass

    @abstractmethod
    async def query_logs(
        self,
        tenant_id: str,
        workspace_id: UUID | None = None,
        actor_id: UUID | None = None,
        action_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit logs with filters."""
        pass


class ObjectStoragePort(ABC):
    """Port for object storage operations."""

    @abstractmethod
    async def upload_immutable(
        self,
        file_path: str,
        tenant_id: str,
        content_type: str,
    ) -> tuple[str, str]:
        """Upload a file as immutable and return (uri, sha256_hash)."""
        pass

    @abstractmethod
    async def download(
        self,
        uri: str,
        local_path: str,
    ) -> None:
        """Download a file from storage."""
        pass

    @abstractmethod
    async def get_metadata(
        self,
        uri: str,
    ) -> dict[str, Any]:
        """Get file metadata from storage."""
        pass

    @abstractmethod
    async def delete(
        self,
        uri: str,
    ) -> None:
        """Delete a file from storage (should use tombstone, not actual delete)."""
        pass


class NotificationPort(ABC):
    """Port for sending notifications."""

    @abstractmethod
    async def send_notification(
        self,
        recipient_id: UUID,
        message: str,
        notification_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send a notification to a user."""
        pass


class SearchPort(ABC):
    """Port for search operations (RAG integration)."""

    @abstractmethod
    async def index_document(
        self,
        tenant_id: str,
        workspace_id: UUID,
        document_id: UUID,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        """Index a document for search."""
        pass

    @abstractmethod
    async def search(
        self,
        tenant_id: str,
        workspace_id: UUID,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for documents."""
        pass
