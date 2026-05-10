"""
Alibaba z-image-turbo client — DashScope multimodal-generation API.

Two modes controlled by prompt_extend:
  False → standard ($0.015/img, faster)
  True  → think/enhanced ($0.03/img, LLM prompt rewrite before generation)
"""

from __future__ import annotations

import json

from app.application.ports.ai_client import AIClient, AIMessage, AIResponse, ImageGenerationResult
from app.core.logging import get_logger

logger = get_logger(__name__)

_DASHSCOPE_IMAGE_URL = (
    "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/"
    "multimodal-generation/generation"
)


class ZImageTurboClient(AIClient):
    """
    Calls DashScope multimodal-generation/generation endpoint with model=z-image-turbo.
    prompt_extend=True activates LLM prompt enhancement (think mode).
    """

    def __init__(self, api_key: str, prompt_extend: bool = False) -> None:
        self._api_key = api_key
        self._prompt_extend = prompt_extend

    # ─── Text / vision — not applicable for image-only model ─────────────────

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        raise NotImplementedError("z-image-turbo is an image generation model only.")

    async def vision_complete(
        self,
        messages: list[AIMessage],
        image_paths: list[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        raise NotImplementedError("z-image-turbo is an image generation model only.")

    # ─── Image generation ─────────────────────────────────────────────────────

    async def generate_image(self, prompt: str, size: str = "1024x1024", **kwargs) -> ImageGenerationResult:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("httpx is required: pip install httpx") from exc

        # Clamp prompt to 800 chars (API limit)
        prompt = prompt[:800]

        payload = {
            "model": "z-image-turbo",
            "input": {
                "messages": [
                    {"role": "user", "content": [{"text": prompt}]}
                ]
            },
            "parameters": {
                "prompt_extend": self._prompt_extend,
                "size": _dashscope_size(size),
            },
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(_DASHSCOPE_IMAGE_URL, json=payload, headers=headers)
            if response.is_error:
                raise RuntimeError(
                    f"z-image-turbo request failed {response.status_code}: {response.text[:500]}"
                )
            data = response.json()

        image_url = _extract_image_url(data)
        if not image_url:
            raise RuntimeError(f"z-image-turbo returned no image URL. Response: {json.dumps(data)[:500]}")

        mode = "think" if self._prompt_extend else "standard"
        logger.info("z-image-turbo [%s] generated image: %s", mode, image_url[:80])
        return ImageGenerationResult(image_path=image_url, provider="alibaba", model="z-image-turbo")


def _extract_image_url(data: dict) -> str | None:
    """Parse DashScope multimodal response to find the image URL."""
    try:
        choices = data["output"]["choices"]
        for choice in choices:
            content = choice["message"]["content"]
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "image" in part:
                        return part["image"]
            elif isinstance(content, str):
                return content
    except (KeyError, IndexError, TypeError):
        pass
    return None


def _dashscope_size(size: str) -> str:
    """DashScope Z-Image expects width*height, while app defaults use widthxheight."""
    normalized = (size or "1024x1024").lower().replace("×", "x")
    if "x" in normalized:
        width, height = normalized.split("x", 1)
        if width.isdigit() and height.isdigit():
            return f"{width}*{height}"
    return size or "1024*1024"
