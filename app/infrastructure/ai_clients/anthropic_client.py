"""
Anthropic Claude provider adapter.
"""

from __future__ import annotations

import base64
from pathlib import Path

from app.application.ports.ai_client import AIClient, AIMessage, AIResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnthropicClient(AIClient):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package is required: pip install anthropic") from exc

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        payload = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        system_msg = next((m.content for m in messages if m.role == "system"), None)

        kwargs_full = {"temperature": temperature, "max_tokens": max_tokens}
        if system_msg:
            kwargs_full["system"] = system_msg

        response = await self._client.messages.create(
            model=self.model, messages=payload, **kwargs_full
        )
        return AIResponse(
            content=response.content[0].text if response.content else "",
            model=self.model,
            provider="anthropic",
            tokens_used=(
                response.usage.input_tokens + response.usage.output_tokens
                if response.usage else None
            ),
        )

    async def vision_complete(
        self,
        messages: list[AIMessage],
        image_paths: list[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        image_content = []
        for path in image_paths:
            p = Path(path)
            if p.exists():
                data = base64.standard_b64encode(p.read_bytes()).decode()
                suffix = p.suffix.lstrip(".") or "jpeg"
                image_content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": f"image/{suffix}", "data": data},
                })

        text_parts = [{"type": "text", "text": m.content} for m in messages]
        payload = [{"role": "user", "content": image_content + text_parts}]

        response = await self._client.messages.create(
            model=self.model,
            messages=payload,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return AIResponse(
            content=response.content[0].text if response.content else "",
            model=self.model,
            provider="anthropic",
        )

    async def generate_image(self, prompt: str, **kwargs) -> "ImageGenerationResult":
        from app.infrastructure.ai_clients._image_result import ImageGenerationResult

        raise NotImplementedError(
            "Anthropic does not support image generation. "
            "Configure an OpenAI provider for the 'image_generation' feature."
        )
