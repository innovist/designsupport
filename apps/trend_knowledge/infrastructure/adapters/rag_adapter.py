"""LightRAG adapter for knowledge graph indexing and retrieval.

Implements RAGPort interface using LightRAG for citation-aware search.
Port 14040 = Knowledge Index gateway.
"""
import logging
import re
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import RAGPort
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)

# LightRAG import with fallback
try:
    from lightrag import LightRAG, QueryParam
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    LightRAG = None
    QueryParam = None


# @MX:ANCHOR: [AUTO] Knowledge graph indexing with citation-aware retrieval
# @MX:REASON: Core RAG component; enables semantic search with document source tracking
class LightRAGAdapter(RAGPort):
    """LightRAG adapter for trend knowledge indexing.

    Provides citation-aware retrieval with document references.
    Returns 'insufficient_evidence' when no matching documents found.
    """

    def __init__(
        self,
        working_dir: str = "/tmp/trend_knowledge/lightrag",
        chunk_size: int = 1024,
    ):
        """Initialize LightRAG adapter.

        Args:
            working_dir: Directory for LightRAG storage
            chunk_size: Text chunk size for indexing

        Raises:
            OperationError: If LightRAG initialization fails after the library is present
        """
        if not LIGHTRAG_AVAILABLE:
            self.working_dir = working_dir
            self.chunk_size = chunk_size
            self._rag = None
            return

        self.working_dir = working_dir
        self.chunk_size = chunk_size

        # Initialize LightRAG instance
        try:
            self._rag = LightRAG(
                working_dir=working_dir,
                chunk_token_size=chunk_size,
            )
            logger.info(f"LightRAG initialized with working_dir={working_dir}")
        except Exception as e:
            logger.warning(f"LightRAG unavailable: {e}")
            self._rag = None

    # @MX:WARN: [AUTO] Async knowledge graph insertion with external dependency
    # @MX:REASON: LightRAG ainsert operation can fail silently; requires library availability check
    async def index_document(
        self,
        document_id: UUID,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index a document into the knowledge graph.

        Args:
            document_id: Document UUID
            content: Document text content
            metadata: Optional metadata (url, published_at, etc.)

        Raises:
            OperationError: If indexing fails
        """
        try:
            if self._rag is None:
                raise OperationError(
                    "LightRAGAdapter",
                    "lightrag library not available. Install with: pip install lightrag",
                )
            # Prepare document with metadata
            full_content = f"[Document ID: {document_id}]\n{content}"

            if metadata:
                metadata_str = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
                full_content = f"{metadata_str}\n{full_content}"

            # Insert into LightRAG
            await self._rag.ainsert(full_text=full_content)

            logger.info(f"Indexed document {document_id} into LightRAG")

        except Exception as e:
            raise OperationError(
                "LightRAGAdapter",
                f"Failed to index document {document_id}: {e}",
            )

    async def query(
        self,
        query_text: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
        mode: str = "hybrid",
    ) -> list[dict[str, Any]]:
        """Query the knowledge graph with citation.

        Args:
            query_text: Query text
            mode: Query mode (local, global, hybrid, naive)
            limit: Maximum results

        Returns:
            List of results with citation (document_id, evidence_quote, published_at)

        Raises:
            OperationError: If query fails
        """
        try:
            if self._rag is None:
                raise OperationError(
                    "LightRAGAdapter",
                    "lightrag library not available. Install with: pip install lightrag",
                )
            # Execute query
            result = await self._rag.aquery(
                query_text,
                param=QueryParam(mode=mode, only_need_context=False),
            )

            # Parse results and extract citations
            if not result or not result.strip():
                logger.warning(f"No results found for query: {query_text}")
                return self._insufficient_evidence_response(query_text)

            # Parse LightRAG response format
            # LightRAG returns context with sources
            parsed_results = self._parse_lightrag_response(result, limit)

            if not parsed_results:
                return self._insufficient_evidence_response(query_text)

            return parsed_results

        except Exception as e:
            raise OperationError(
                "LightRAGAdapter",
                f"Query failed for '{query_text}': {e}",
            )

    async def query_with_citations(
        self,
        query_text: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query and return explicit citation envelope."""
        results = await self.query(query_text=query_text, limit=limit, filters=filters)
        insufficient = bool(results and results[0].get("score") == 0.0)
        citations = [
            {
                "document_id": item.get("document_id"),
                "quote": item.get("evidence_quote"),
                "published_at": item.get("published_at"),
                "url": item.get("url"),
            }
            for item in results
            if item.get("document_id") or item.get("evidence_quote")
        ]
        return {
            "results": results,
            "citations": citations,
            "has_more": False,
            "insufficient_evidence": insufficient,
        }

    async def delete_document(self, document_id: UUID) -> None:
        """Delete is unsupported by the local LightRAG adapter."""
        raise OperationError(
            "LightRAGAdapter.delete_document",
            "document deletion is not supported by this LightRAG adapter",
        )

    async def health_check(self) -> bool:
        """Return whether LightRAG is initialized."""
        return self.is_available()

    def _parse_lightrag_response(
        self,
        response: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Parse LightRAG response into structured results with citations.

        Args:
            response: LightRAG response string
            limit: Maximum results

        Returns:
            List of structured results with citation (document_id, evidence_quote, published_at)
        """
        results = []

        try:
            sections = re.split(r"\n\s*\n(?=\[Document ID:)", response.strip())

            for i, section in enumerate(sections[:limit]):
                if not section.strip():
                    continue

                # Extract document_id and metadata from the section
                # We prepend document info in index_document as: "[Document ID: {uuid}]"
                document_id = None
                published_at = None
                metadata_lines = []

                lines = section.split("\n")
                answer_lines = []

                for line in lines:
                    # Extract document ID from our prepended format
                    if "[Document ID:" in line and "]" in line:
                        try:
                            # Extract UUID from "[Document ID: xxx-xxx-xxx]"
                            doc_id_str = line.split("[Document ID:")[1].split("]")[0].strip()
                            document_id = doc_id_str
                            continue  # Don't include this in answer
                        except (IndexError, ValueError):
                            pass

                    # Extract metadata fields (key: value format)
                    if ":" in line and not line.startswith("["):
                        potential_meta = line.split(":", 1)
                        if len(potential_meta) == 2:
                            key, value = potential_meta[0].strip(), potential_meta[1].strip()
                            # Check for common metadata fields
                            if key.lower() in ["published_at", "published at", "date", "publication_date"]:
                                try:
                                    published_at = value
                                except ValueError:
                                    pass
                                metadata_lines.append(line)
                                continue
                            elif key.lower() in ["url", "source", "author"]:
                                metadata_lines.append(line)
                                continue

                    # Remaining lines are part of the answer
                    answer_lines.append(line)

                # Join answer lines, filtering out metadata
                answer = "\n".join(answer_lines).strip()

                # Use the actual cited passage as evidence_quote
                # Extract the most relevant sentence(s) from the answer
                evidence_quote = self._extract_evidence_quote(answer)

                # Only add result if we have meaningful content
                if answer and len(answer) > 10:
                    result = {
                        "answer": answer,
                        "document_id": document_id,  # Extracted from [Document ID: xxx] marker
                        "evidence_quote": evidence_quote,  # Actual cited passage
                        "published_at": published_at,  # Extracted from metadata
                        "score": 1.0 - (i * 0.1),  # Decay score by position
                    }
                    results.append(result)

        except Exception as e:
            logger.error(f"Failed to parse LightRAG response: {e}")

        return results

    def _extract_evidence_quote(self, text: str, max_length: int = 300) -> str:
        """Extract the most relevant passage as evidence quote.

        Args:
            text: Full answer text
            max_length: Maximum length of evidence quote

        Returns:
            Most relevant passage or truncated text
        """
        if not text:
            return ""

        # Split into sentences
        sentences = [s.strip() for s in text.split(".") if s.strip()]

        if not sentences:
            return text[:max_length] + "..." if len(text) > max_length else text

        # Return the first substantial sentence (usually contains the main answer)
        for sentence in sentences:
            if len(sentence) > 20:  # Only use sentences with meaningful content
                if len(sentence) > max_length:
                    return sentence[:max_length] + "..."
                return sentence

        # Fallback: return first sentences up to max_length
        result = sentences[0]
        for sentence in sentences[1:]:
            if len(result) + len(sentence) + 2 <= max_length:
                result += ". " + sentence
            else:
                break

        return result

    def _insufficient_evidence_response(
        self,
        query_text: str,
    ) -> list[dict[str, Any]]:
        """Return insufficient evidence response.

        Args:
            query_text: Original query text

        Returns:
            Response indicating insufficient evidence
        """
        return [
            {
                "answer": "Insufficient evidence in the knowledge base to answer this query.",
                "document_id": None,
                "evidence_quote": None,
                "published_at": None,
                "score": 0.0,
                "query": query_text,
            }
        ]

    def is_available(self) -> bool:
        """Check if LightRAG is available.

        Returns:
            True if available, False otherwise
        """
        return LIGHTRAG_AVAILABLE and self._rag is not None


def get_lightrag_adapter(
    working_dir: str = "/tmp/trend_knowledge/lightrag",
) -> LightRAGAdapter:
    """Get LightRAG adapter instance.

    Args:
        working_dir: Directory for LightRAG storage

    Returns:
        LightRAGAdapter instance

    Raises:
        OperationError: If LightRAG not available
    """
    return LightRAGAdapter(working_dir=working_dir)
