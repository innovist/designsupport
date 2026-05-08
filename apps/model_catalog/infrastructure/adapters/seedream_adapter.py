"""ByteDance Seedream image provider adapter for model catalog.

Implements REQ-04-ADAPTER-001: Provider adapter for image generation.
Implements REQ-04-POLICY-007: Primary provider = ByteDance Seedream 4.5.

CRITICAL: Do NOT duplicate /api/v3 in the path. base_url already includes it.
"""
import os
from typing import Any

import httpx

from apps.model_catalog.domain.entities import ModelProvider, ModelCatalog
from apps.model_catalog.application.ports import ProviderAdapterPort
from shared.domain.exceptions import OperationError


class SeedreamAdapter(ProviderAdapterPort):
    """Adapter for ByteDance Seedream 4.5 via BytePlus Ark API.

    Environment variables:
        BYTEDANCE_SEEDREAM_API_KEY: API key for authentication

    CRITICAL: base_url from ModelProvider already includes /api/v3.
    Do NOT duplicate it when building the request URL.
    """

    DEFAULT_COST_PER_1K_INPUT = 0.01
    DEFAULT_COST_PER_1K_OUTPUT = 0.02

    def __init__(
        self,
        provider: ModelProvider,
        model: ModelCatalog,
    ):
        """Initialize Seedream adapter.

        Args:
            provider: Provider configuration from database
            model: Model configuration from database

        Raises:
            OperationError: If API key not found in environment
        """
        self.provider = provider
        self.model = model

        # Get API key from environment (via provider.api_key_env)
        self.api_key = os.getenv(provider.api_key_env)
        if not self.api_key:
            raise OperationError(
                "SeedreamAdapter",
                f"{provider.api_key_env} environment variable not set",
            )

        # Build base URL and endpoint
        # CRITICAL: Do NOT duplicate /api/v3 - provider.base_url already includes it
        self.base_url = (provider.base_url or "https://ark.ap-southeast.bytepluses.com/api/v3").rstrip("/")
        self.endpoint = provider.endpoint_path or "/images/generations"

    async def call_model(
        self,
        _provider: ModelProvider,
        _model: ModelCatalog,
        payload: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Call Seedream image generation API.

        Args:
            _provider: Provider config (unused, instance fields used instead)
            _model: Model config (unused, instance fields used instead)
            payload: Request payload with 'prompt' key
            options: Additional options (size, n, response_format, etc.)

        Returns:
            Response dictionary with usage metrics

        Raises:
            OperationError: If API call fails
        """
        try:
            # Build request URL
            # CRITICAL: Do NOT duplicate /api/v3 - base_url already includes it
            url = f"{self.base_url}{self.endpoint}"

            # Extract prompt from payload
            prompt = payload.get("prompt", "")
            if not prompt:
                raise OperationError("SeedreamAdapter", "Prompt is required in payload")

            # Build request body
            request_payload = {
                "model": options.get("model", "seedream-4.5-turbo"),
                "prompt": prompt,
                "size": options.get("size", "1024x1024"),
                "n": options.get("n", 1),
                "response_format": options.get("response_format", "url"),
            }

            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
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
                raise OperationError("SeedreamAdapter", "No image data in response")

            image_data = data["data"][0]

            # Build response with usage metrics
            return {
                "images": [
                    {
                        "url": image_data.get("url"),
                        "b64_json": image_data.get("b64_json"),
                    }
                ],
                "usage": {
                    "prompt_tokens": len(prompt.split()),  # Rough estimate
                    "completion_tokens": 100,  # Fixed for image generation
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
                "SeedreamAdapter",
                f"HTTP error {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            raise OperationError("SeedreamAdapter", str(e))

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD.

        Args:
            prompt_tokens: Input tokens
            completion_tokens: Output tokens

        Returns:
            Cost in USD
        """
        input_cost = (prompt_tokens / 1000.0) * self.DEFAULT_COST_PER_1K_INPUT
        output_cost = (completion_tokens / 1000.0) * self.DEFAULT_COST_PER_1K_OUTPUT
        return round(input_cost + output_cost, 6)
