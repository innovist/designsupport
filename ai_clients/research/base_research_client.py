"""
Base Research Client - Abstract interface for AI research/search services
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class ResearchSource(Enum):
    """Research source identifiers"""
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"
    GLM = "glm"


@dataclass
class ResearchResult:
    """AI research result data class"""
    source: ResearchSource           # Research source
    query: str                       # Original research query
    content: str                     # Research result content
    citations: List[str] = field(default_factory=list)  # Source URLs
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model: str = ""                  # Model used for research
    metadata: dict = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "source": self.source.value,
            "query": self.query,
            "content": self.content,
            "citations": self.citations,
            "timestamp": self.timestamp,
            "model": self.model,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchResult":
        """Create from dictionary"""
        return cls(
            source=ResearchSource(data.get("source", "glm")),
            query=data.get("query", ""),
            content=data.get("content", ""),
            citations=data.get("citations", []),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            model=data.get("model", ""),
            metadata=data.get("metadata", {})
        )


class BaseResearchClient(ABC):
    """Base class for AI research clients"""

    def __init__(self):
        from app.core.logging import get_logger
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def research(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ResearchResult:
        """
        Perform web research using AI search capabilities

        Args:
            query: Research query string
            context: Additional context for the research

        Returns:
            ResearchResult with content and citations
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if API key is configured and service is available"""
        pass

    def _build_prompt(self, query: str, context: Optional[str] = None) -> str:
        """Build research prompt with context"""
        base_prompt = (
            "You are a fashion trend research expert. "
            "Search for and analyze current fashion trends, "
            "focusing on the specific query below. "
            "Provide comprehensive insights with citations."
        )

        if context:
            return f"{base_prompt}\n\nContext: {context}\n\nQuery: {query}"
        return f"{base_prompt}\n\nQuery: {query}"

    def _extract_citations(self, response_text: str) -> List[str]:
        """Extract citation URLs from response text"""
        import re
        # Common URL patterns in AI responses
        url_pattern = r'https?://[^\s\])\}"\'>]+'
        urls = re.findall(url_pattern, response_text)
        return list(set(urls))  # Remove duplicates
