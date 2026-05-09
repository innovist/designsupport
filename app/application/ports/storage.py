"""
Abstract port for file storage operations.
"""

from abc import ABC, abstractmethod


class StorageClient(ABC):

    @abstractmethod
    async def save(self, data: bytes, path: str) -> str:
        """Persist bytes to storage and return the saved path."""

    @abstractmethod
    async def load(self, path: str) -> bytes:
        """Load and return bytes from the given path."""

    @abstractmethod
    def url(self, path: str) -> str:
        """Return a publicly accessible URL for the stored file."""
