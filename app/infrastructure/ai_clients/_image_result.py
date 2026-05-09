"""
Shared result type for image generation responses.
"""

from pydantic import BaseModel


class ImageGenerationResult(BaseModel):
    image_path: str
    provider: str
    model: str
