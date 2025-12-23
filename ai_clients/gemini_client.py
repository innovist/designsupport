"""
Gemini client facade
"""

from typing import Optional

from ai_clients.gemini_core import GeminiClientCore
from ai_clients.gemini_extras import GeminiClientExtras
from ai_clients.gemini_types import GenerationConfig, GenerationResponse


class GeminiClient(GeminiClientCore, GeminiClientExtras):
    """Unified Gemini client"""


_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


async def get_gemini_client_dep():
    client = get_gemini_client()
    try:
        yield client
    finally:
        await client.cleanup()


__all__ = [
    "GeminiClient",
    "GenerationConfig",
    "GenerationResponse",
    "get_gemini_client",
    "get_gemini_client_dep"
]
