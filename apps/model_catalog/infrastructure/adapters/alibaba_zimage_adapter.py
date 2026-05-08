"""Alibaba Z-Image provider adapter for model catalog.

Implements REQ-04-ADAPTER-001: Provider adapter for image generation.
Implements REQ-04-POLICY-007: Fallback provider = Alibaba Z-Image Turbo.
"""
import os
from typing import Any

import httpx

from apps.model_catalog.domain.entities import ModelProvider, ModelCatalog
from apps.model_catalog.application.ports import ProviderAdapterPort
from shared.domain.exceptions import OperationError


class AlibabaZImageAdapter(ProviderAdapterPort):
    """Adapter for Alibaba Z-Image Turbo API.

    Environment variables:
        ALIBABA_API_KEY: API key for authentication
    """

    DEFAULT_COST_PER_1K_INPUT = 0.008
    DEFAULT_COST_PER_1K_OUTPUT = 0.015

    def __init__(
        self,
        provider: ModelProvider,
        model: ModelCatalog,
    ):
        """Initialize Alibaba Z-Image adapter.

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
                "AlibabaZImageAdapter",
                f"{provider.api_key_env} environment variable not set",
            )

        # Build base URL and endpoint
        self.base_url = provider.base_url or "https://dashscope.aliyuncs.com/api/v1"
        self.endpoint = provider.endpoint_path or "/services/aigc/text2image/image-synthesis"

    async def call_model(
        self,
        _provider: ModelProvider,
        _model: ModelCatalog,
        payload: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Call Alibaba Z-Image generation API.

        Args:
            _provider: Provider config (unused, instance fields used instead)
            _model: Model config (unused, instance fields used instead)
            payload: Request payload with 'prompt' key
            options: Additional options (size, n, etc.)

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
                raise OperationError("AlibabaZImageAdapter", "Prompt is required in payload")

            # Build request body for Alibaba Z-Image
            request_payload = {
                "model": "z-image-turbo",
                "input": {
                    "prompt": prompt,
                },
                "parameters": {
                    "size": options.get("size", "1024*1024"),
                    "n": options.get("n", 1),
                },
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

            # Extract image data (Alibaba format)
            if "output" not in data or "results" not in data["output"]:
                raise OperationError("AlibabaZImageAdapter", "No image data in response")

            image_results = data["output"]["results"]

            # Build response with usage metrics
            return {
                "images": [
                    {
                        "url": result.get("url"),
                        "b64_json": result.get("b64_image"),
                    }
                    for result in image_results
                ],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
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
                "AlibabaZImageAdapter",
                f"HTTP error {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            raise OperationError("AlibabaZImageAdapter", str(e))

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD."""
        input_cost = (prompt_tokens / 1000.0) * self.DEFAULT_COST_PER_1K_INPUT
        output_cost = (completion_tokens / 1000.0) * self.DEFAULT_COST_PER_1K_OUTPUT
        return round(input_cost + output_cost, 6)
