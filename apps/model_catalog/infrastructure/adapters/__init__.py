"""Provider adapters for model catalog.

Implements REQ-04-ADAPTER-001: Adapters for external provider APIs.
"""
from apps.model_catalog.infrastructure.adapters.seedream_adapter import SeedreamAdapter
from apps.model_catalog.infrastructure.adapters.alibaba_zimage_adapter import AlibabaZImageAdapter
from apps.model_catalog.infrastructure.adapters.gemini_image_adapter import GeminiImageAdapter
from apps.model_catalog.infrastructure.adapters.openai_image_adapter import OpenAIImageAdapter

__all__ = [
    "SeedreamAdapter",
    "AlibabaZImageAdapter",
    "GeminiImageAdapter",
    "OpenAIImageAdapter",
]
