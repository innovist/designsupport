"""
OpenAI provider adapter (text + vision completion, image generation).
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from app.application.ports.ai_client import AIClient, AIMessage, AIResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient(AIClient):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None, **kwargs) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is required: pip install openai") from exc

        client_kwargs: dict = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**client_kwargs)
        self.model = model
        self.default_params = kwargs

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        # Exclude temperature/max_tokens from default_params to avoid duplicate keyword arg error
        extra = {k: v for k, v in self.default_params.items() if k not in ("temperature", "max_tokens")}
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=payload,
            temperature=temperature,
            max_tokens=max_tokens,
            **{**extra, **kwargs},
        )
        choice = response.choices[0]
        return AIResponse(
            content=choice.message.content or "",
            model=self.model,
            provider="openai",
            tokens_used=response.usage.total_tokens if response.usage else None,
        )

    async def vision_complete(
        self,
        messages: list[AIMessage],
        image_paths: list[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        image_parts = []
        for path in image_paths:
            p = Path(path)
            if p.exists():
                data = base64.b64encode(p.read_bytes()).decode()
                suffix = p.suffix.lstrip(".") or "jpeg"
                image_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{suffix};base64,{data}"},
                })
            else:
                image_parts.append({"type": "image_url", "image_url": {"url": path}})

        content_parts = image_parts + [
            {"type": "text", "text": m.content} for m in messages
        ]
        payload = [{"role": "user", "content": content_parts}]

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=payload,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return AIResponse(
            content=choice.message.content or "",
            model=self.model,
            provider="openai",
            tokens_used=response.usage.total_tokens if response.usage else None,
        )

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> "ImageGenerationResult":
        """Generate an image using DALL-E and return a result object."""
        from app.infrastructure.ai_clients._image_result import ImageGenerationResult

        response = await self._client.images.generate(
            model=self.model,
            prompt=prompt,
            n=1,
            size=size,
        )
        image_url = response.data[0].url
        return ImageGenerationResult(image_path=image_url, provider="openai", model=self.model)
