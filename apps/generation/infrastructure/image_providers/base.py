"""Base image provider adapter."""
from abc import ABC, abstractmethod

from shared.application.result import Result


class ImageProviderPort(ABC):
    """Abstract port for image generation providers.

    All image provider adapters must implement this interface.
    """

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        n: int = 1,
        **kwargs
    ) -> Result:
        """Generate an image from a text prompt.

        Args:
            prompt: Text description of the desired image
            size: Image size (e.g., "1024x1024", "512x512")
            n: Number of images to generate
            **kwargs: Provider-specific parameters

        Returns:
            Result containing:
                - asset_uri: URL or path to generated image
                - cost_meta: CostMetadata for the generation
            or error details
        """
        pass

    @abstractmethod
    def get_model_key(self) -> str:
        """Get the model key for this provider.

        Returns:
            Model identifier (e.g., "seedream-4.5")
        """
        pass

    @abstractmethod
    def estimate_cost(self) -> float:
        """Estimate generation cost per image in USD."""
        pass
