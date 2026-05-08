"""
Gemini Research Client - Grounding with Google Search
Uses Gemini 2.5 Flash with Google Search grounding capability
"""

import asyncio
from typing import Optional

from .base_research_client import BaseResearchClient, ResearchResult, ResearchSource


class GeminiResearchClient(BaseResearchClient):
    """Gemini Grounding with Google Search client"""

    def __init__(self):
        super().__init__()
        self._client = None
        self._model_name = "gemini-2.5-flash"

    def _get_client(self):
        """Lazy load Gemini client"""
        if self._client is None:
            try:
                from google import genai
                from app.core.settings_storage import get_api_key
                api_key = get_api_key("gemini")
                if not api_key:
                    self.logger.warning("Gemini API key not configured")
                    return None
                self._client = genai.Client(api_key=api_key)
            except ImportError as e:
                self.logger.error(f"google-genai package not available: {e}")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if Gemini API key is configured"""
        from app.core.settings_storage import get_api_key
        return bool(get_api_key("gemini"))

    async def research(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ResearchResult:
        """
        Perform research using Gemini with Google Search grounding

        Args:
            query: Research query
            context: Additional context

        Returns:
            ResearchResult with grounded search results
        """
        client = self._get_client()
        if not client:
            return ResearchResult(
                source=ResearchSource.GEMINI,
                query=query,
                content="",
                model=self._model_name
            )

        try:
            from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

            prompt = self._build_prompt(query, context)

            # Use async properly - run in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=GenerateContentConfig(
                        tools=[Tool(google_search=GoogleSearch())]
                    )
                )
            )

            content = response.text if hasattr(response, 'text') else ""

            # Extract citations from grounding metadata
            citations = []
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'grounding_metadata'):
                        gm = candidate.grounding_metadata
                        if hasattr(gm, 'search_entry_point') and gm.search_entry_point:
                            if hasattr(gm.search_entry_point, 'rendered_content'):
                                citations.extend(
                                    self._extract_citations(gm.search_entry_point.rendered_content)
                                )

            return ResearchResult(
                source=ResearchSource.GEMINI,
                query=query,
                content=content,
                citations=citations,
                model=self._model_name,
                metadata={"grounding_enabled": True}
            )

        except Exception as e:
            self.logger.error(f"Gemini research failed: {e}")
            return ResearchResult(
                source=ResearchSource.GEMINI,
                query=query,
                content="",
                model=self._model_name,
                metadata={"error": str(e)}
            )
