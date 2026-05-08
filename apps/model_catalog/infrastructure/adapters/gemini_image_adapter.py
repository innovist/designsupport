"""Google Gemini image provider adapter for model catalog.

Implements REQ-04-ADAPTER-001: Provider adapter for image generation.
Implements REQ-04-POLICY-007: Fallback provider = Google Gemini 3.1 Flash Image Preview.
"""
import os
from typing import Any

import httpx

from apps.model_catalog.domain.entities import ModelProvider, ModelCatalog
from apps.model_catalog.application.ports import ProviderAdapterPort
from shared.domain.exceptions import OperationError


class GeminiImageAdapter(ProviderAdapterPort):
    """Adapter for Google Gemini image generation API.

    Environment variables:
        GEMINI_API_KEYS: API key for authentication (comma-separated list)
    """

    DEFAULT_COST_PER_1K_INPUT = 0.001
    DEFAULT_COST_PER_1K_OUTPUT = 0.002

    def __init__(
        self,
        provider: ModelProvider,
        model: ModelCatalog,
    ):
        """Initialize Gemini image adapter.

        Args:
            provider: Provider configuration from database
            model: Model configuration from database

        Raises:
            OperationError: If API key not found in environment
        """
        self.provider = provider
        self.model = model

        # Get API key from environment (support comma-separated list)
        api_keys = os.getenv(provider.api_key_env, "")
        self.api_key = api_keys.split(",")[0].strip() if api_keys else None

        if not self.api_key:
            raise OperationError(
                "GeminiImageAdapter",
                f"{provider.api_key_env} environment variable not set",
            )

        # Build base URL and endpoint
        self.base_url = provider.base_url or "https://generativelanguage.googleapis.com/v1beta"
        self.endpoint = provider.endpoint_path or f"/models/{model.model_name}:generateContent"

    async def call_model(
        self,
        _provider: ModelProvider,
        _model: ModelCatalog,
        payload: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Call Gemini image generation API.

        Args:
            _provider: Provider config (unused, instance fields used instead)
            _model: Model config (unused, instance fields used instead)
            payload: Request payload with 'prompt' key
            options: Additional options (size, etc.)

        Returns:
            Response dictionary with usage metrics

        Raises:
            OperationError: If API call fails
        """
        try:
            # Build request URL (append API key as query param for Gemini)
            url = f"{self.base_url}{self.endpoint}?key={self.api_key}"

            # Extract prompt from payload
            prompt = payload.get("prompt", "")
            if not prompt:
                raise OperationError("GeminiImageAdapter", "Prompt is required in payload")

            # Parse size option
            size = options.get("size", "1024x1024")
            _width, _height = map(int, size.lower().replace("x", "*").split("*"))

            # Build request body for Gemini API
            request_payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt,
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "imageGenerationMode": "image-only",
                    "responseMimeType": "image/png",
                    "responseSchema": {
                        "type": "string",
                        "format": "base64",
                    },
                },
            }

            # Make API request
            headers = {
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    json=request_payload,
                    headers=headers,
                )
                response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract image data (Gemini format)
            if "candidates" not in data or len(data["candidates"]) == 0:
                raise OperationError("GeminiImageAdapter", "No image data in response")

            candidate = data["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                raise OperationError("GeminiImageAdapter", "Invalid response format")

            # Extract base64 image data
            image_data = None
            for part in candidate["content"]["parts"]:
                if "inlineData" in part:
                    image_data = part["inlineData"].get("data")
                    break

            if not image_data:
                raise OperationError("GeminiImageAdapter", "No base64 image data in response")

            # Build response with usage metrics
            return {
                "images": [
                    {
                        "b64_json": image_data,
                        "url": None,
                    }
                ],
                "usage": {
                    "prompt_tokens": data.get("usageMetadata", {}).get("promptTokenCount", len(prompt.split())),
                    "completion_tokens": data.get("usageMetadata", {}).get("candidatesTokenCount", 100),
                    "total_tokens": data.get("usageMetadata", {}).get("totalTokenCount", len(prompt.split()) + 100),
                    "estimated_cost": self._calculate_cost(
                        data.get("usageMetadata", {}).get("promptTokenCount", len(prompt.split())),
                        data.get("usageMetadata", {}).get("candidatesTokenCount", 100),
                    ),
                },
                "model": self.model.model_name,
            }

        except httpx.HTTPStatusError as e:
            raise OperationError(
                "GeminiImageAdapter",
                f"HTTP error {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            raise OperationError("GeminiImageAdapter", str(e))

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD."""
        input_cost = (prompt_tokens / 1000.0) * self.DEFAULT_COST_PER_1K_INPUT
        output_cost = (completion_tokens / 1000.0) * self.DEFAULT_COST_PER_1K_OUTPUT
        return round(input_cost + output_cost, 6)
