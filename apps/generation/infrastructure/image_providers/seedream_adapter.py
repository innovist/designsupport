"""ByteDance Seedream 4.5 image provider adapter.

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


class SeedreamAdapter:
    """Adapter for ByteDance Seedream 4.5 via BytePlus Ark.

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
        self.api_key = None
        self.base_url = provider.base_url or "https://ark.ap-southeast.bytepluses.com/api/v3"
        self.endpoint_path = provider.endpoint_path or "/images/generations"

        # Validate URL construction
        if self.base_url.endswith(self.endpoint_path):
            # Avoid duplication if base_url already contains endpoint
            self.full_url = self.base_url
        elif self.base_url.endswith("/"):
            self.full_url = f"{self.base_url}{self.endpoint_path[1:]}"  # Remove leading /
        else:
            self.full_url = f"{self.base_url}{self.endpoint_path}"

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
                "SeedreamAdapter._get_api_key",
                f"API key not found in environment variable: {self.provider.api_key_env}",
            )
        return api_key

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        n: int = 1,
        **kwargs,
    ) -> Result:
        """Generate an image using Seedream 4.5.

        Args:
            prompt: Text description of the desired image
            size: Image size (e.g., "1024x1024", "512x512")
            n: Number of images to generate
            **kwargs: Provider-specific parameters

        Returns:
            Result containing:
                - asset_uri: URL to generated image
                - cost_meta: CostMetadata for the generation
            or error details

        Raises:
            OperationError: If API call fails or returns invalid response
        """
        try:
            api_key = self.api_key or self._get_api_key()
            self.api_key = api_key
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Prepare request payload
                payload = {
                    "model": self.model.model_name,
                    "prompt": prompt,
                    "size": size,
                    "n": n,
                }

                # Add any additional parameters from kwargs
                payload.update(kwargs)

                # Make API request
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                logger.info(f"Calling Seedream API: {self.full_url}")
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
                        error_detail = error_json.get("error", error_detail)
                    except Exception:
                        pass

                    raise OperationError(
                        "SeedreamAdapter.generate_image",
                        f"API request failed with status {response.status_code}: {error_detail}",
                    )

                # Parse response
                response_data = response.json()

                # Extract image URL from response
                if "data" not in response_data or not response_data["data"]:
                    raise OperationError(
                        "SeedreamAdapter.generate_image",
                        "Invalid response format: missing 'data' field",
                    )

                image_data = response_data["data"][0]
                image_url = image_data.get("url")

                if not image_url:
                    raise OperationError(
                        "SeedreamAdapter.generate_image",
                        "Invalid response format: missing image URL",
                    )

                # Calculate cost estimate
                cost_meta = self._calculate_cost(prompt, response_data)

                # Return success result
                return Result.success(
                    {
                        "asset_uri": image_url,
                        "cost_meta": cost_meta,
                        "raw_response": response_data,
                    }
                )

        except httpx.TimeoutException:
            logger.error("Seedream API request timed out")
            raise OperationError(
                "SeedreamAdapter.generate_image",
                "API request timed out after 60 seconds",
            )
        except httpx.HTTPError as e:
            logger.error(f"Seedream API HTTP error: {e}")
            raise OperationError(
                "SeedreamAdapter.generate_image",
                f"HTTP error occurred: {str(e)}",
            )
        except OperationError:
            # Re-raise OperationError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in SeedreamAdapter.generate_image: {e}")
            raise OperationError(
                "SeedreamAdapter.generate_image",
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
        usage = response_data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", len(prompt) // 4)  # Rough estimate
        total_tokens = usage.get("total_tokens", prompt_tokens)

        # Cost per image (approximate based on typical BytePlus pricing)
        cost_per_image = 0.02  # $0.02 per image
        cost_usd = usage.get("estimated_cost", cost_per_image)

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
            Model identifier (e.g., "seedream-4.5")
        """
        return self.model.model_name

    def estimate_cost(self) -> float:
        """Estimate generation cost per image in USD."""
        return 0.02
