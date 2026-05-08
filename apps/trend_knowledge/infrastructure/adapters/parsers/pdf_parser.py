"""PDF parser adapter using pypdf.

Extracts text from PDF files.
Returns None on failure (NO fake text).
"""
import os
from logging import getLogger
from typing import Any

# pypdf import with fallback
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None

logger = getLogger(__name__)


class PDFParser:
    """Parse PDF files using pypdf."""

    def __init__(self) -> None:
        """Initialize parser."""
        if not PYPDF_AVAILABLE:
            logger.warning("pypdf not available. PDF parsing disabled.")

    async def parse_file(
        self,
        file_path: str,
        file_type: str | None = None,
    ) -> str | None:
        """Parse PDF file and extract text.

        Args:
            file_path: Path to PDF file
            file_type: Optional file type hint (ignored, always PDF)

        Returns:
            Extracted text content or None if parsing fails

        Raises:
            ValueError: If file is not a valid PDF
        """
        if not PYPDF_AVAILABLE:
            logger.error("pypdf not available")
            return None

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        try:
            # Open PDF
            reader = PdfReader(file_path)

            # Validate PDF
            if len(reader.pages) == 0:
                logger.warning(f"PDF has no pages: {file_path}")
                return None

            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue

            if not text_parts:
                logger.warning(f"No text extracted from PDF: {file_path}")
                return None

            full_text = "\n\n".join(text_parts)
            logger.info(
                f"Extracted {len(full_text)} characters from {len(text_parts)} pages "
                f"of {file_path}"
            )
            return full_text

        except Exception as e:
            logger.error(f"PDF parsing failed for {file_path}: {e}")
            # Return None instead of fake text
            return None

    async def detect_type(self, file_path: str) -> str | None:
        """Detect if file is PDF.

        Args:
            file_path: Path to file

        Returns:
            "pdf" if PDF file, None otherwise
        """
        if not os.path.exists(file_path):
            return None

        _, ext = os.path.splitext(file_path)
        if ext.lower() == ".pdf":
            return "pdf"

        return None


def get_pdf_parser() -> PDFParser:
    """Get singleton PDFParser instance.

    Returns:
        PDFParser instance
    """
    return PDFParser()
