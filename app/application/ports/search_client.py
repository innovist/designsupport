"""
Abstract port for web / image search clients.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: str | None = None


class ImageSearchResult(BaseModel):
    title: str
    url: str
    image_url: str
    source_domain: str


class SearchClient(ABC):

    @abstractmethod
    async def web_search(self, query: str, num_results: int = 10) -> list[WebSearchResult]:
        """Perform a web search and return structured results."""

    @abstractmethod
    async def image_search(self, query: str, num_results: int = 10) -> list[ImageSearchResult]:
        """Perform an image search and return structured results."""
