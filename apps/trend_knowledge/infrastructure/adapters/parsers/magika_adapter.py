"""Magika file type detector adapter stub.

Implements file type detection using Google's Magika.
This is a stub - actual implementation requires magika package.

REQ-02-FILE-001: File type detection via Magika for 1000+ file types.

To use this adapter:
1. Install magika: pip install magika
2. Implement detect_type() using Magika's deep learning model
3. Update ParserPort factory to use Magika for type detection

Reference: https://github.com/google/magika
"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class MagikaAdapter:
    """File type detector using Google's Magika.

    Magika provides:
    - Deep learning-based file type detection
    - Support for 1000+ file types
    - High accuracy (>99%) for common formats
    - Fast prediction (<5ms per file)

    This is a stub implementation.
    """

    def __init__(self, model_path: str | None = None):
        """Initialize Magika adapter.

        Args:
            model_path: Optional path to custom Magika model
        """
        self.model_path = model_path
        logger.warning(
            "MagikaAdapter is a stub. "
            "Install magika to use this adapter: pip install magika"
        )

    async def detect_type(self, file_path: str) -> str | None:
        """Detect file type using Magika.

        Args:
            file_path: Path to file

        Returns:
            Detected file type (e.g., "pdf", "hwp", "docx") or None

        Raises:
            NotImplementedError: Until magika is installed
        """
        raise NotImplementedError(
            "MagikaAdapter requires magika package. "
            "Install with: pip install magika\n"
            "Then implement using Magika model for file type detection.\n"
            "Reference: https://github.com/google/magika\n\n"
            "Example usage:\n"
            "  from magika import Magika\n"
            "  magika = Magika()\n"
            "  result = magika.identify(file_path)\n"
            "  return result.output.ct_label"
        )

    async def is_supported(self, file_path: str) -> bool:
        """Check if file type is supported for parsing.

        Args:
            file_path: Path to file

        Returns:
            True if file type is supported, False otherwise

        Raises:
            NotImplementedError: Until magika is installed
        """
        raise NotImplementedError(
            "MagikaAdapter requires magika package. "
            "Install with: pip install magika"
        )


def get_magika_detector() -> MagikaAdapter:
    """Get singleton MagikaAdapter instance.

    Returns:
        MagikaAdapter instance
    """
    return MagikaAdapter()
