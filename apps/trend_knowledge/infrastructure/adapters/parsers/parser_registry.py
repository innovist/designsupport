"""Parser registry for selecting appropriate parser.

Routes file parsing to the correct parser based on detected file type.
Implements ParserPort interface.
"""
import logging
from typing import Any
from uuid import UUID

from apps.trend_knowledge.application.ports import ParserPort
from apps.trend_knowledge.infrastructure.adapters.file_type_detector import (
    get_file_type_detector,
)
from apps.trend_knowledge.infrastructure.adapters.parsers.doc_parser import (
    get_doc_parser,
)
from apps.trend_knowledge.infrastructure.adapters.parsers.pdf_parser import (
    get_pdf_parser,
)
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)


class ParserRegistry(ParserPort):
    """Registry for selecting appropriate parser.

    Detects file type using Magika and routes to specialized parser.
    Supports PDF, HWP, HWPX, DOCX formats.
    """

    # File type to parser mapping
    PARSER_MAPPING = {
        "pdf": "pdf",
        "hwp": "doc",
        "hwpx": "doc",
        "docx": "doc",
        "application/pdf": "pdf",
    }

    def __init__(self):
        """Initialize parser registry with all parsers."""
        self._detector = get_file_type_detector()
        self._pdf_parser = get_pdf_parser()
        self._doc_parser = get_doc_parser()

    async def parse_file(
        self,
        file_path: str,
        file_type: str | None = None,
    ) -> str:
        """Parse a file and extract text content.

        Args:
            file_path: Path to file to parse
            file_type: Optional file type hint (detected via Magika if None)

        Returns:
            Extracted text content

        Raises:
            OperationError: If parsing fails
        """
        # Detect file type if not provided
        if file_type is None:
            file_type = await self.detect_type(file_path)

        if file_type is None:
            raise OperationError(
                "ParserRegistry",
                f"Failed to detect file type for: {file_path}",
            )

        # Route to appropriate parser
        parser_type = self.PARSER_MAPPING.get(file_type)

        if parser_type == "pdf":
            result = await self._pdf_parser.parse_file(file_path, file_type)
        elif parser_type == "doc":
            result = await self._doc_parser.parse_file(file_path, file_type)
        else:
            raise OperationError(
                "ParserRegistry",
                f"Unsupported file type: {file_type}",
            )

        # Check if parsing succeeded
        if result is None:
            raise OperationError(
                "ParserRegistry",
                f"Parser returned None for {file_path} (type: {file_type})",
            )

        return result

    async def detect_type(
        self,
        file_path: str,
    ) -> str:
        """Detect file type using Magika.

        Args:
            file_path: Path to file

        Returns:
            Detected file type (pdf, hwp, hwpx, docx, etc.)

        Raises:
            OperationError: If detection fails
        """
        detected_type = await self._detector.detect_type(file_path)

        if detected_type is None:
            # Fallback to extension-based detection
            import os

            _, ext = os.path.splitext(file_path)
            ext = ext.lower().lstrip(".")

            if ext in ["pdf", "hwp", "hwpx", "docx"]:
                return ext

            raise OperationError(
                "ParserRegistry",
                f"Failed to detect file type for: {file_path}",
            )

        return detected_type


def get_parser_registry() -> ParserRegistry:
    """Get singleton ParserRegistry instance.

    Returns:
        ParserRegistry instance
    """
    return ParserRegistry()
