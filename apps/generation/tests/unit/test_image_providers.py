"""Unit tests for image provider adapters."""
import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Setup Django before imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, "/Volumes/KevinData/Office/00. HoneyMnB/30. Coding_Project/32. MoChang/DesignSupport")

import django
django.setup()

from apps.generation.domain.entities import CostMetadata
from apps.model_catalog.domain.entities import ModelCatalog, ModelProvider, AuthScheme
from shared.application.result import Result
from shared.domain.exceptions import OperationError


@pytest.fixture
def sample_provider():
    """Create a sample ModelProvider entity."""
    return ModelProvider(
        id="prov-test",
        name="test_provider",
        api_key_env="TEST_API_KEY",
        base_url="https://api.test.com/v1",
        endpoint_path="/images/generations",
        auth_scheme=AuthScheme.BEARER,
        active=True,
    )


@pytest.fixture
def sample_model():
    """Create a sample ModelCatalog entity."""
    return ModelCatalog(
        id="mdl-test",
        provider_id="prov-test",
        model_name="test-model",
        type="image",
        context_limit=None,
        cost_estimate=0.02,
        modalities=["image"],
        active=True,
    )


class TestSeedreamAdapter:
    """Tests for SeedreamAdapter."""

    @pytest.mark.asyncio
    async def test_generate_image_success(self, sample_provider, sample_model):
        """Test successful image generation."""
        from apps.generation.infrastructure.image_providers.seedream_adapter import SeedreamAdapter

        # Mock environment variable
        with patch.dict("os.environ", {"TEST_API_KEY": "test-key-123"}):
            adapter = SeedreamAdapter(sample_provider, sample_model)

            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"url": "https://example.com/generated-image.png"}],
                "usage": {
                    "prompt_tokens": 10,
                    "total_tokens": 10,
                    "estimated_cost": 0.02,
                },
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_http_client = AsyncMock()
                mock_http_client.__aenter__.return_value = mock_http_client
                mock_http_client.post.return_value = mock_response
                mock_client.return_value = mock_http_client

                result = await adapter.generate_image(
                    prompt="A beautiful sunset",
                    size="1024x1024",
                    n=1,
                )

                assert result.is_success
                assert result.value["asset_uri"] == "https://example.com/generated-image.png"
                assert isinstance(result.value["cost_meta"], CostMetadata)
                assert result.value["cost_meta"].model_key == "test-model"
                assert result.value["cost_meta"].cost_usd == 0.02

    @pytest.mark.asyncio
    async def test_generate_image_missing_api_key(self, sample_provider, sample_model):
        """Test image generation fails when API key is missing."""
        from apps.generation.infrastructure.image_providers.seedream_adapter import SeedreamAdapter

        with patch.dict("os.environ", {}, clear=True):
            adapter = SeedreamAdapter(sample_provider, sample_model)

            with pytest.raises(OperationError) as exc_info:
                await adapter.generate_image(prompt="test")

            assert "API key not found" in str(exc_info.value)

    def test_get_model_key(self, sample_provider, sample_model):
        """Test get_model_key returns correct model name."""
        from apps.generation.infrastructure.image_providers.seedream_adapter import SeedreamAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
            adapter = SeedreamAdapter(sample_provider, sample_model)
            assert adapter.get_model_key() == "test-model"

    def test_estimate_cost(self, sample_provider, sample_model):
        """Test cost estimation."""
        from apps.generation.infrastructure.image_providers.seedream_adapter import SeedreamAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
            adapter = SeedreamAdapter(sample_provider, sample_model)
            cost = adapter.estimate_cost()
            assert cost == 0.02


class TestAlibabaZImageAdapter:
    """Tests for AlibabaZImageAdapter."""

    @pytest.mark.asyncio
    async def test_generate_image_success(self, sample_provider, sample_model):
        """Test successful image generation."""
        from apps.generation.infrastructure.image_providers.alibaba_zimage_adapter import AlibabaZImageAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key-123"}):
            adapter = AlibabaZImageAdapter(sample_provider, sample_model)

            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"url": "https://example.com/alibaba-image.png"}],
                "usage": {
                    "prompt_tokens": 10,
                    "total_tokens": 10,
                    "estimated_cost": 0.015,
                },
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_http_client = AsyncMock()
                mock_http_client.__aenter__.return_value = mock_http_client
                mock_http_client.post.return_value = mock_response
                mock_client.return_value = mock_http_client

                result = await adapter.generate_image(
                    prompt="A futuristic city",
                    size="1024x1024",
                    n=1,
                )

                assert result.is_success
                assert result.value["asset_uri"] == "https://example.com/alibaba-image.png"
                assert result.value["cost_meta"].cost_usd == 0.015

    def test_estimate_cost(self, sample_provider, sample_model):
        """Test cost estimation."""
        from apps.generation.infrastructure.image_providers.alibaba_zimage_adapter import AlibabaZImageAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
            adapter = AlibabaZImageAdapter(sample_provider, sample_model)
            cost = adapter.estimate_cost()
            assert cost == 0.015


class TestGeminiImageAdapter:
    """Tests for GeminiImageAdapter."""

    @pytest.mark.asyncio
    async def test_generate_image_success(self, sample_provider, sample_model):
        """Test successful image generation with base64 response."""
        from apps.generation.infrastructure.image_providers.gemini_image_adapter import GeminiImageAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key-123"}):
            adapter = GeminiImageAdapter(sample_provider, sample_model)

            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": "image/png",
                                        "data": "base64encodeddata",
                                    }
                                }
                            ]
                        }
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "totalTokenCount": 10,
                },
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_http_client = AsyncMock()
                mock_http_client.__aenter__.return_value = mock_http_client
                mock_http_client.post.return_value = mock_response
                mock_client.return_value = mock_http_client

                result = await adapter.generate_image(
                    prompt="A mountain landscape",
                    size="1024x1024",
                    n=1,
                )

                assert result.is_success
                assert result.value["asset_uri"].startswith("data:image/png;base64,")
                assert result.value["cost_meta"].cost_usd == 0.01

    def test_estimate_cost(self, sample_provider, sample_model):
        """Test cost estimation."""
        from apps.generation.infrastructure.image_providers.gemini_image_adapter import GeminiImageAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
            adapter = GeminiImageAdapter(sample_provider, sample_model)
            cost = adapter.estimate_cost()
            assert cost == 0.01


class TestOpenAIImageAdapter:
    """Tests for OpenAIImageAdapter."""

    @pytest.mark.asyncio
    async def test_generate_image_success(self, sample_provider, sample_model):
        """Test successful image generation."""
        from apps.generation.infrastructure.image_providers.openai_image_adapter import OpenAIImageAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key-123"}):
            adapter = OpenAIImageAdapter(sample_provider, sample_model)

            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [{"url": "https://example.com/openai-image.png"}],
                "usage": {
                    "prompt_tokens": 10,
                    "total_tokens": 10,
                    "estimated_cost": 0.04,
                },
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_http_client = AsyncMock()
                mock_http_client.__aenter__.return_value = mock_http_client
                mock_http_client.post.return_value = mock_response
                mock_client.return_value = mock_http_client

                result = await adapter.generate_image(
                    prompt="A abstract art piece",
                    size="1024x1024",
                    n=1,
                )

                assert result.is_success
                assert result.value["asset_uri"] == "https://example.com/openai-image.png"
                assert result.value["cost_meta"].cost_usd == 0.04

    def test_estimate_cost(self, sample_provider, sample_model):
        """Test cost estimation."""
        from apps.generation.infrastructure.image_providers.openai_image_adapter import OpenAIImageAdapter

        with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):
            adapter = OpenAIImageAdapter(sample_provider, sample_model)
            cost = adapter.estimate_cost()
            assert cost == 0.04
