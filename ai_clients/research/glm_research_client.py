"""
GLM Research Client - Web Research Tool
Uses GLM-4.7 with built-in web search capability (OpenAI-compatible API)
"""

import asyncio
import json
from typing import Optional

from .base_research_client import BaseResearchClient, ResearchResult, ResearchSource


FASHION_RESEARCH_SYSTEM_PROMPT = (
    "You are a fashion trend research expert. "
    "Search for and analyze current fashion trends, "
    "focusing on specific queries. "
    "Provide comprehensive insights with proper citations."
)


class GLMResearchClient(BaseResearchClient):
    """GLM web research client (OpenAI-compatible API)"""

    def __init__(self):
        super().__init__()
        self._client = None
        self._model_name = "glm-4.7"
        self._base_url = "https://api.z.ai/api/coding/paas/v4"

    def _get_client(self):
        """Lazy load GLM client (OpenAI-compatible)"""
        if self._client is None:
            try:
                from openai import OpenAI
                from app.core.settings_storage import get_api_key
                api_key = get_api_key("glm")
                if not api_key:
                    self.logger.warning("GLM API key not configured")
                    return None
                self._client = OpenAI(api_key=api_key, base_url=self._base_url)
            except ImportError as e:
                self.logger.error(f"openai package not available: {e}")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if GLM API key is configured"""
        from app.core.settings_storage import get_api_key
        return bool(get_api_key("glm"))

    async def research(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ResearchResult:
        """
        Perform research using GLM with web search tool

        Note: Current GLM API uses OpenAI-compatible interface.
        Web search is enabled server-side based on the model configuration.
        """
        client = self._get_client()
        if not client:
            return ResearchResult(
                source=ResearchSource.GLM,
                query=query,
                content="",
                model=self._model_name
            )

        try:
            prompt = self._build_prompt(query, context)

            # Run in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": FASHION_RESEARCH_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ]
                )
            )

            content = ""
            citations = []

            # Extract content from response
            if response.choices:
                message = response.choices[0].message
                if hasattr(message, 'content'):
                    content = message.content or ""

            # Extract URLs from content
            if content:
                citations = self._extract_citations(content)

            return ResearchResult(
                source=ResearchSource.GLM,
                query=query,
                content=content,
                citations=citations,
                model=self._model_name
            )

        except Exception as e:
            self.logger.error(f"GLM research failed: {e}")
            return ResearchResult(
                source=ResearchSource.GLM,
                query=query,
                content="",
                model=self._model_name,
                metadata={"error": str(e)}
            )
