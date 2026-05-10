"""
Google Gemini image generation client.

Uses google-genai SDK with generate_content + response_modalities=["IMAGE"].
Returns base64 data URL since the API returns inline bytes, not a hosted URL.
"""

from __future__ import annotations

import base64
from pathlib import Path

from app.application.ports.ai_client import AIClient, AIMessage, AIResponse, ImageGenerationResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiImageClient(AIClient):
    """
    Generates images via Gemini models that support IMAGE response modality
    (e.g. gemini-2.5-flash-image, gemini-3.1-flash-image-preview).

    Response is a base64 data URL stored in ImageGenerationResult.image_path.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    # ─── Text / vision — not applicable ──────────────────────────────────────

    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        raise NotImplementedError("GeminiImageClient is for image generation only.")

    async def vision_complete(
        self,
        messages: list[AIMessage],
        image_paths: list[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        raise NotImplementedError("GeminiImageClient is for image generation only.")

    # ─── Image generation ─────────────────────────────────────────────────────

    async def generate_image(self, prompt: str, size: str = "1024x1024", **kwargs) -> ImageGenerationResult:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai package is required: pip install google-genai") from exc

        client = genai.Client(api_key=self._api_key)

        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        )

        contents: list[object] = [prompt]
        for image_path in kwargs.get("reference_image_paths") or []:
            path = Path(image_path)
            if not path.exists():
                raise ValueError(f"Reference image file not found: {image_path}")
            contents.append(
                types.Part.from_bytes(
                    data=path.read_bytes(),
                    mime_type=_mime_type_for_path(path),
                )
            )

        response = await client.aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )

        image_bytes, mime_type = _extract_image_bytes(response)
        if not image_bytes:
            raise RuntimeError(
                f"Gemini image model '{self._model}' returned no image. "
                "Ensure the model supports IMAGE modality."
            )

        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
        logger.info("Gemini image [%s] generated, size=%d bytes", self._model, len(image_bytes))
        return ImageGenerationResult(image_path=data_url, provider="gemini", model=self._model)


def _extract_image_bytes(response: object) -> tuple[bytes | None, str]:
    """Extract inline image bytes and mime_type from a GenerateContentResponse."""
    try:
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    return part.inline_data.data, (part.inline_data.mime_type or "image/png")
    except (AttributeError, IndexError, TypeError):
        pass
    return None, "image/png"


def _mime_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"
