"""OpenAI GPT-Image-2 provider adapter for model catalog.

Implements REQ-04-ADAPTER-001: Provider adapter for image generation.
Implements REQ-04-POLICY-007: Fallback provider = OpenAI GPT-Image-2.
"""
import os
from typing import Any

import httpx

from apps.model_catalog.domain.entities import ModelProvider, ModelCatalog
from apps.model_catalog.application.ports import ProviderAdapterPort
from shared.domain.exceptions import OperationError


class OpenAIImageAdapter(ProviderAdapterPort):
    """Adapter for OpenAI GPT-Image-2 API.

    Environment variables:
        OPENAI_API_KEY: API key for authentication
    """

    DEFAULT_COST_PER_1K_INPUT = 0.015
    DEFAULT_COST_PER_1K_OUTPUT = 0.03

    def __init__(
        self,
        provider: ModelProvider,
        model: ModelCatalog,
    ):
        """Initialize OpenAI image adapter.

        Args:
            provider: Provider configuration from database
            model: Model configuration from database

        Raises:
            OperationError: If API key not found in environment
        """
        self.provider = provider
        self.model = model

        # Get API key from environment
        self.api_key = os.getenv(provider.api_key_env)
        if not self.api_key:
            raise OperationError(
                "OpenAIImageAdapter",
                f"{provider.api_key_env} environment variable not set",
            )

        # Build base URL and endpoint
        self.base_url = provider.base_url or "https://api.openai.com/v1"
        self.endpoint = provider.endpoint_path or "/images/generations"

    async def call_model(
        self,
        provider: ModelProvider,
        model: ModelCatalog,
        payload: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Call OpenAI image generation API.

        Args:
            provider: Provider configuration (not used, self.provider is used)
            model: Model configuration (not used, self.model is used)
            payload: Request payload with 'prompt' key
            options: Additional options (size, n, quality, etc.)

        Returns:
            Response dictionary with usage metrics

        Raises:
            OperationError: If API call fails
        """
        try:
            # Build request URL
            url = f"{self.base_url}{self.endpoint}"

            # Extract prompt from payload
            prompt = payload.get("prompt", "")
            if not prompt:
                raise OperationError("OpenAIImageAdapter", "Prompt is required in payload")

            # Build request body for OpenAI Images API
            request_payload = {
                "model": options.get("model", "gpt-image-2"),
                "prompt": prompt,
                "size": options.get("size", "1024x1024"),
                "n": options.get("n", 1),
                "response_format": options.get("response_format", "url"),
            }

            # Add quality option for supported models
            if "quality" in options:
                request_payload["quality"] = options["quality"]

            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
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

            # Extract image data
            if "data" not in data or len(data["data"]) == 0:
                raise OperationError("OpenAIImageAdapter", "No image data in response")

            # Build response with usage metrics
            images = []
            for item in data["data"]:
                images.append({
                    "url": item.get("url"),
                    "b64_json": item.get("b64_json"),
                })

            return {
                "images": images,
                "usage": {
                    "prompt_tokens": len(prompt.split()),  # OpenAI doesn't return token count for images
                    "completion_tokens": 100,
                    "total_tokens": len(prompt.split()) + 100,
                    "estimated_cost": self._calculate_cost(
                        len(prompt.split()),
                        100,
                    ),
                },
                "model": self.model.model_name,
            }

        except httpx.HTTPStatusError as e:
            raise OperationError(
                "OpenAIImageAdapter",
                f"HTTP error {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            raise OperationError("OpenAIImageAdapter", str(e))

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD.

        Note: OpenAI Images API pricing is per image, not per token.
        This is a simplified estimation.
        """
        # For 1024x1024 image: $0.040 (standard) or $0.080 (hd)
        # For smaller sizes: ~50% of standard price
        size_multiplier = 1.0  # Default 1024x1024

        # Estimate based on prompt complexity (rough approximation)
        input_cost = (prompt_tokens / 1000.0) * self.DEFAULT_COST_PER_1K_INPUT
        output_cost = 0.040 * size_multiplier  # Fixed cost per image

        return round(input_cost + output_cost, 6)
