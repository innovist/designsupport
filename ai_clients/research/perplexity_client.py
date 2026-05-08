"""
Perplexity Research Client - Sonar API
Uses Perplexity Sonar models with web search capabilities
"""

import asyncio
from typing import Optional

from .base_research_client import BaseResearchClient, ResearchResult, ResearchSource


FASHION_RESEARCH_SYSTEM_PROMPT = (
    "You are a fashion trend research expert. "
    "Search for and analyze current fashion trends, "
    "focusing on specific queries. "
    "Provide comprehensive insights with proper citations."
)


class PerplexityClient(BaseResearchClient):
    """Perplexity Sonar API client for web research"""

    def __init__(self, model: str = "sonar"):
        super().__init__()
        self._client = None
        self._model = model  # sonar or sonar-pro

    def _get_client(self):
        """Lazy load Perplexity client (OpenAI-compatible API)"""
        if self._client is None:
            try:
                from openai import OpenAI
                from app.core.settings_storage import get_api_key
                api_key = get_api_key("perplexity")
                if not api_key:
                    self.logger.warning("Perplexity API key not configured")
                    return None
                self._client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.perplexity.ai"
                )
            except ImportError as e:
                self.logger.error(f"openai package not available: {e}")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if Perplexity API key is configured"""
        from app.core.settings_storage import get_api_key
        return bool(get_api_key("perplexity"))

    async def research(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ResearchResult:
        """
        Perform research using Perplexity Sonar API

        Args:
            query: Research query
            context: Additional context

        Returns:
            ResearchResult with citations
        """
        client = self._get_client()
        if not client:
            return ResearchResult(
                source=ResearchSource.PERPLEXITY,
                query=query,
                content="",
                model=self._model
            )

        try:
            prompt = self._build_prompt(query, context)

            # Run in thread pool for OpenAI client
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": FASHION_RESEARCH_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    search_recency_filter="month",  # Recent data (1 month)
                    search_domain_filter=["fashion", "style", "clothing", "trends"]
                )
            )

            content = ""
            citations = []

            if response.choices:
                content = response.choices[0].message.content or ""

            # Extract citations from response
            if hasattr(response, 'citations') and response.citations:
                citations = [c.get("url", "") for c in response.citations if c.get("url")]

            # Also extract URLs from content
            if content:
                citations.extend(self._extract_citations(content))
                citations = list(set(citations))  # Remove duplicates

            return ResearchResult(
                source=ResearchSource.PERPLEXITY,
                query=query,
                content=content,
                citations=citations,
                model=self._model
            )

        except Exception as e:
            self.logger.error(f"Perplexity research failed: {e}")
            return ResearchResult(
                source=ResearchSource.PERPLEXITY,
                query=query,
                content="",
                model=self._model,
                metadata={"error": str(e)}
            )
