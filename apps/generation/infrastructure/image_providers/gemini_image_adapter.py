"""Google Gemini image provider adapter.

Implements REQ-03-GEN-006: All model calls go through SPEC-04 ModelRouter.
"""
import logging
from typing import Any

import httpx

from apps.generation.domain.entities import CostMetadata
from apps.model_catalog.domain.entities import ModelCatalog, ModelProvider
from shared.application.result import Result
from shared.domain.exceptions import OperationError

logger = logging.getLogger(__name__)


class GeminiImageAdapter:
    """Adapter for Google Gemini image generation.

    Implements ImageProviderPort interface for image generation.
    """

    def __init__(self, provider: ModelProvider, model: ModelCatalog):
        """Initialize the adapter with provider and model configuration.

        Args:
            provider: ModelProvider entity with API configuration
            model: ModelCatalog entity with model details
        """
        self.provider = provider
        self.model = model
        self.api_key = self._get_api_key()
        self.base_url = provider.base_url or "https://generativelanguage.googleapis.com/v1beta"
        self.endpoint_path = provider.endpoint_path or f"/models/{self.model.model_name}:generateContent"

        # Validate URL construction
        if self.base_url.endswith(self.endpoint_path):
            self.full_url = f"{self.base_url}?key={self.api_key}"
        elif self.base_url.endswith("/"):
            self.full_url = f"{self.base_url}{self.endpoint_path[1:]}?key={self.api_key}"
        else:
            self.full_url = f"{self.base_url}{self.endpoint_path}?key={self.api_key}"

    def _get_api_key(self) -> str:
        """Get API key from environment variable.

        Returns:
            API key string

        Raises:
            OperationError: If API key not found in environment
        """
        import os

        api_key = os.environ.get(self.provider.api_key_env)
        if not api_key:
            raise OperationError(
                "GeminiImageAdapter._get_api_key",
                f"API key not found in environment variable: {self.provider.api_key_env}",
            )
        return api_key

    async def generate_image(
        self,
        prompt: str,
        **kwargs,
    ) -> Result:
        """Generate an image using Gemini.

        Args:
            prompt: Text description of the desired image
            size: Image size (e.g., "1024x1024", "512x512")
            n: Number of images to generate
            **kwargs: Provider-specific parameters

        Returns:
            Result containing:
                - asset_uri: URL to generated image (base64 data URL)
                - cost_meta: CostMetadata for the generation
            or error details

        Raises:
            OperationError: If API call fails or returns invalid response
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Prepare request payload for Gemini API
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": kwargs.get("temperature", 0.4),
                        "topK": kwargs.get("top_k", 32),
                        "topP": kwargs.get("top_p", 1.0),
                        "maxOutputTokens": kwargs.get("max_output_tokens", 2048),
                    }
                }

                # Make API request
                headers = {
                    "Content-Type": "application/json",
                }

                logger.info(f"Calling Gemini API: {self.full_url}")
                response = await client.post(
                    self.full_url,
                    json=payload,
                    headers=headers,
                )

                # Handle HTTP errors
                if response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("error", {}).get("message", error_detail)
                    except Exception:
                        pass

                    raise OperationError(
                        "GeminiImageAdapter.generate_image",
                        f"API request failed with status {response.status_code}: {error_detail}",
                    )

                # Parse response
                response_data = response.json()

                # Extract image data from Gemini response
                if "candidates" not in response_data or not response_data["candidates"]:
                    raise OperationError(
                        "GeminiImageAdapter.generate_image",
                        "Invalid response format: missing 'candidates' field",
                    )

                candidate = response_data["candidates"][0]
                if "content" not in candidate or "parts" not in candidate["content"]:
                    raise OperationError(
                        "GeminiImageAdapter.generate_image",
                        "Invalid response format: missing content data",
                    )

                # Gemini returns base64 encoded image data
                parts = candidate["content"]["parts"]
                image_data = None
                for part in parts:
                    if "inlineData" in part:
                        image_data = part["inlineData"]
                        break

                if not image_data or "data" not in image_data:
                    raise OperationError(
                        "GeminiImageAdapter.generate_image",
                        "Invalid response format: missing image data",
                    )

                # Create base64 data URL
                mime_type = image_data.get("mimeType", "image/png")
                base64_data = image_data["data"]
                asset_uri = f"data:{mime_type};base64,{base64_data}"

                # Calculate cost estimate
                cost_meta = self._calculate_cost(prompt, response_data)

                # Return success result
                return Result.success(
                    {
                        "asset_uri": asset_uri,
                        "cost_meta": cost_meta,
                        "raw_response": response_data,
                    }
                )

        except httpx.TimeoutException:
            logger.error("Gemini API request timed out")
            raise OperationError(
                "GeminiImageAdapter.generate_image",
                "API request timed out after 60 seconds",
            )
        except httpx.HTTPError as e:
            logger.error(f"Gemini API HTTP error: {e}")
            raise OperationError(
                "GeminiImageAdapter.generate_image",
                f"HTTP error occurred: {str(e)}",
            )
        except OperationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in GeminiImageAdapter.generate_image: {e}")
            raise OperationError(
                "GeminiImageAdapter.generate_image",
                f"Unexpected error: {str(e)}",
            )

    def _calculate_cost(self, prompt: str, response_data: dict[str, Any]) -> CostMetadata:
        """Calculate cost metadata for the generation.

        Args:
            prompt: The generation prompt
            response_data: Raw API response data

        Returns:
            CostMetadata instance
        """
        # Extract usage information from response if available
        usage_metadata = response_data.get("usageMetadata", {})
        prompt_tokens = usage_metadata.get("promptTokenCount", len(prompt) // 4)
        total_tokens = usage_metadata.get("totalTokenCount", prompt_tokens)

        # Cost per image (Gemini: approximately $0.01 per image for flash model)
        cost_per_image = 0.01
        cost_usd = usage_metadata.get("estimatedCost", cost_per_image)

        return CostMetadata(
            model_key=self.model.model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
        )

    def get_model_key(self) -> str:
        """Get the model key for this provider.

        Returns:
            Model identifier (e.g., "gemini-3.1-flash-image-preview")
        """
        return self.model.model_name

    def estimate_cost(self) -> float:
        """Estimate generation cost per image in USD."""
        return 0.01
