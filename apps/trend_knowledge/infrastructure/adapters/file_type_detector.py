"""File type detector adapter using Magika.

Detects MIME types from file paths.
Returns None on failure (no guessing).
"""
import os
from logging import getLogger
from typing import Any

# Magika import with fallback
try:
    from magika import Magika
    MAGIKA_AVAILABLE = True
except ImportError:
    MAGIKA_AVAILABLE = False
    Magika = None

logger = getLogger(__name__)


class FileTypeDetector:
    """Detect file types using Magika."""

    def __init__(self) -> None:
        """Initialize detector with Magika client."""
        if not MAGIKA_AVAILABLE:
            logger.warning("Magika not available. File type detection disabled.")
            self._client = None
            return

        try:
            self._client = Magika()
            logger.info("FileTypeDetector initialized with Magika")
        except Exception as e:
            logger.error(f"Failed to initialize Magika: {e}")
            self._client = None

    async def detect_type(self, file_path: str) -> str | None:
        """Detect file type from path.

        Args:
            file_path: Path to file

        Returns:
            Detected MIME type or None if detection fails
        """
        if self._client is None:
            logger.warning("Magika client not available, returning None")
            return None

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        try:
            # Magika prediction
            result = self._client.identify_path(file_path)
            if result and result.output:
                detected_type = result.output.ct_label
                logger.debug(f"Detected type: {detected_type} for {file_path}")
                return detected_type
            else:
                logger.warning(f"Magika returned no result for {file_path}")
                return None

        except Exception as e:
            logger.error(f"File type detection failed for {file_path}: {e}")
            # Return None instead of guessing
            return None

    def is_available(self) -> bool:
        """Check if Magika is available."""
        return self._client is not None


# Singleton instance
_detector_instance: FileTypeDetector | None = None


def get_file_type_detector() -> FileTypeDetector:
    """Get singleton FileTypeDetector instance.

    Returns:
        FileTypeDetector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FileTypeDetector()
    return _detector_instance
