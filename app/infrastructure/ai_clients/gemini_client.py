"""
Google Gemini provider adapter (text + vision completion).
"""

from __future__ import annotations

import base64
from pathlib import Path

from app.application.ports.ai_client import AIClient, AIMessage, AIResponse, ImageGenerationResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiClient(AIClient):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro", **kwargs) -> None:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "google-generativeai package is required: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=api_key)
        self._genai = genai
        self.model = model
        self.default_params = kwargs

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        import asyncio

        model = self._genai.GenerativeModel(self.model)
        parts = [m.content for m in messages]

        generation_config = self._genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                " ".join(parts),
                generation_config=generation_config,
            ),
        )

        return AIResponse(
            content=response.text or "",
            model=self.model,
            provider="gemini",
            tokens_used=None,
        )

    async def vision_complete(
        self,
        messages: list[AIMessage],
        image_paths: list[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        import asyncio

        model = self._genai.GenerativeModel(self.model)
        content_parts: list = []

        for path in image_paths:
            p = Path(path)
            if p.exists():
                image_bytes = p.read_bytes()
                suffix = p.suffix.lstrip(".") or "jpeg"
                content_parts.append({
                    "mime_type": f"image/{suffix}",
                    "data": base64.b64encode(image_bytes).decode(),
                })
            # Remote URLs not directly supported; log warning
            else:
                logger.warning("Gemini vision: path %s not found, skipping", path)

        for m in messages:
            content_parts.append(m.content)

        generation_config = self._genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(
                content_parts, generation_config=generation_config
            ),
        )

        return AIResponse(
            content=response.text or "",
            model=self.model,
            provider="gemini",
            tokens_used=None,
        )

    async def generate_image(self, prompt: str, size: str = "1024x1024", **kwargs) -> ImageGenerationResult:
        """Gemini does not natively support image generation - raise clear error."""
        raise NotImplementedError(
            "Gemini does not support image generation via this API. "
            "Configure an OpenAI or compatible provider for the 'image_generation' feature."
        )
