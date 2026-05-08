"""Shared RAG Port Adapter.

Provides RAGPort interface for both trend_knowledge and references modules.
Abstracts LightRAG implementation to allow infrastructure substitution.
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class RAGPort(ABC):
    """Port for RAG (Retrieval-Augmented Generation) operations.

    Abstract interface for LightRAG integration.
    Implemented in infrastructure layer to allow substitution.
    """

    @abstractmethod
    async def index_document(
        self,
        document_id: UUID,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        """Index a document for retrieval.

        Args:
            document_id: Unique document identifier
            content: Document text content
            metadata: Document metadata (title, url, published_at, etc.)
        """
        pass

    @abstractmethod
    async def query(
        self,
        query_text: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query the index for relevant documents.

        Args:
            query_text: Search query
            limit: Maximum number of results
            filters: Optional filters (domain, date_range, etc.)

        Returns:
            List of results with document_id, content, score, metadata
        """
        pass

    @abstractmethod
    async def query_with_citations(
        self,
        query_text: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query with explicit citations per SPEC-02 REQ-02-INDEX-003.

        Args:
            query_text: Search query
            limit: Maximum number of results
            filters: Optional filters

        Returns:
            Dict with:
            - results: List of insights with evidence
            - citations: List of {document_id, quote, published_at, url}
            - has_more: Whether more results exist
            - insufficient_evidence: True if no relevant documents found
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document from the index.

        Args:
            document_id: Document to delete
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if RAG service is healthy.

        Returns:
            True if service is operational
        """
        pass


__all__ = ["RAGPort"]
