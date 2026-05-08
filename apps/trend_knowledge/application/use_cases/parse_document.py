"""Parse document use case.

Detects file type, selects parser, parses content.
On failure: records in ParsingFailureQueue (NO fake text fallback).
"""
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from apps.trend_knowledge.application.ports import (
    ParsingFailureQueueRepositoryPort,
    ParserPort,
    TrendDocumentRepositoryPort,
)
from apps.trend_knowledge.domain.entities import (
    ParsingFailureQueue,
    TrendDocument,
    TrendDocumentStatus,
)
from shared.domain.exceptions import OperationError

logger = getLogger(__name__)


# @MX:ANCHOR: [AUTO] Document parsing entry point with failure queue tracking
# @MX:REASON: Core RAG pipeline component; handles multiple file formats and error recovery
class ParseDocumentUseCase:
    """Parse document and extract text content."""

    def __init__(
        self,
        document_repository: TrendDocumentRepositoryPort,
        parser_port: ParserPort,
        failure_queue_repository: ParsingFailureQueueRepositoryPort,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            document_repository: Repository for document lookup/update
            parser_port: Parser interface for file parsing
            failure_queue_repository: Repository for failure tracking
        """
        self._document_repository = document_repository
        self._parser_port = parser_port
        self._failure_queue_repository = failure_queue_repository

    # @MX:WARN: [AUTO] Async file I/O with external storage dependencies
    # @MX:REASON: Parser failures recorded in failure queue; no fake text fallback per SPEC
    async def execute(self, document_id: UUID) -> dict[str, Any]:
        """Parse a document and extract text content.

        Args:
            document_id: ID of the document to parse

        Returns:
            Updated document metadata

        Raises:
            ValueError: If document not found
            OperationError: If parsing fails (recorded in failure queue)
        """
        # Load document
        document = await self._document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        if document.parse_status != TrendDocumentStatus.RAW.value:
            logger.info(f"Document already parsed: {document_id}")
            return {
                "id": str(document.id),
                "status": document.parse_status,
                "parsed_text_uri": document.parsed_text_uri,
            }

        logger.info(f"Parsing document: {document.id} (uri: {document.raw_uri})")

        try:
            # Detect file type
            file_type = await self._parser_port.detect_type(document.raw_uri)
            logger.debug(f"Detected file type: {file_type}")

            # Parse content
            parsed_text = await self._parser_port.parse_file(
                document.raw_uri,
                file_type=file_type,
            )

            if not parsed_text or not parsed_text.strip():
                raise ValueError("Parser returned empty content")

            parsed_text_uri = await self._persist_parsed_text(document.id, parsed_text)
            document.mark_parsed(parsed_text_uri)

            saved_doc = await self._document_repository.save(document)

            logger.info(f"Successfully parsed document {document_id}: {len(parsed_text)} chars")
            return {
                "id": str(saved_doc.id),
                "status": saved_doc.parse_status,
                "parsed_text_length": len(parsed_text),
                "parsed_text_uri": saved_doc.parsed_text_uri,
            }

        except Exception as e:
            logger.error(f"Parsing failed for document {document_id}: {e}")

            # Record in failure queue
            failure = ParsingFailureQueue(
                document_id=document.id,
                reason=f"{type(e).__name__}: {e}",
            )

            await self._failure_queue_repository.save(failure)

            # Update document status
            document.mark_failed()
            await self._document_repository.save(document)

            raise OperationError("ParseDocument", f"Parsing failed and recorded: {e}") from e

    async def _persist_parsed_text(self, document_id: UUID, parsed_text: str) -> str:
        """Persist extracted text and return a storage URI."""
        from asgiref.sync import sync_to_async
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage

        storage_path = Path("trend_documents") / "parsed" / f"{document_id}.md"
        return await sync_to_async(default_storage.save)(
            str(storage_path),
            ContentFile(parsed_text.encode("utf-8")),
        )
