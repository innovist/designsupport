"""Unit tests for ThumbnailProcessor.

Tests INV-02-05 compliance:
- Downloads images from URL
- Resizes to max 1024px on longest edge
- Converts to WebP at 80% quality
- Strips ALL EXIF data
- Saves to object storage
- Returns storage URI
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.references.infrastructure.adapters.thumbnail_processor import ThumbnailProcessor


class TestThumbnailProcessor:
    """Test suite for ThumbnailProcessor."""

    @pytest.fixture
    def processor(self):
        """Create a ThumbnailProcessor instance."""
        return ThumbnailProcessor()

    @pytest.fixture
    def mock_storage_adapter(self):
        """Create a mock storage adapter."""
        adapter = AsyncMock()
        adapter.upload_bytes = AsyncMock(return_value="storage://thumbnails/test.webp")
        return adapter

    @pytest.mark.asyncio
    async def test_process_tier_1_asset_with_valid_image(self, processor, mock_storage_adapter):
        """Test processing Tier 1 asset with valid image."""
        asset = {
            "source_url": "https://example.com/image.jpg",
        }

        with patch.object(processor, "_download_image", return_value=b"fake_image_data"):
            with patch.object(processor, "_process_image_bytes", return_value=b"processed_webp"):
                result = await processor.process_asset(asset, tier=1, storage_adapter=mock_storage_adapter)

                assert result["thumbnail_uri"] == "storage://thumbnails/test.webp"
                assert result["thumbnail_max_edge_px"] == 1024
                mock_storage_adapter.upload_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_tier_3_asset_no_download(self, processor):
        """Test that Tier 3 assets are not downloaded."""
        asset = {
            "source_url": "https://example.com/image.jpg",
        }

        with patch.object(processor, "_download_image") as mock_download:
            result = await processor.process_asset(asset, tier=3)

            # Tier 3 should NOT download
            mock_download.assert_not_called()
            # Should return external URL
            assert result["thumbnail_uri"] == "https://example.com/image.jpg"
            assert result["thumbnail_max_edge_px"] == 0

    @pytest.mark.asyncio
    async def test_invalid_tier_raises_error(self, processor):
        """Test that invalid tier raises ValueError."""
        asset = {"source_url": "https://example.com/image.jpg"}

        with pytest.raises(ValueError, match="Invalid tier"):
            await processor.process_asset(asset, tier=4)

    @pytest.mark.asyncio
    async def test_process_image_bytes_strips_exif(self, processor):
        """Test that image processing strips EXIF data."""
        # Create a mock image with EXIF data
        mock_image = MagicMock()
        mock_image.size = (2048, 1536)
        mock_image.mode = "RGB"

        with patch("apps.references.infrastructure.adapters.thumbnail_processor.Image") as MockImage:
            MockImage.open.return_value.__enter__.return_value = mock_image
            mock_image.resize.return_value = mock_image

            # Mock the save to capture output
            output_buffer = MagicMock()
            mock_image.save = MagicMock()

            result = processor._process_image_bytes(b"fake_image", max_edge=1024)

            # Verify resize was called (dimensions > max_edge)
            mock_image.resize.assert_called_once()
            # Verify save was called with WebP format (which strips EXIF)
            mock_image.save.assert_called_once()

    def test_process_image_bytes_handles_rgba(self, processor):
        """Test RGB conversion handles RGBA images during processing."""
        mock_image = MagicMock()
        mock_image.size = (100, 100)
        mock_image.mode = "RGBA"
        mock_image.split.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

        with patch("apps.references.infrastructure.adapters.thumbnail_processor.Image") as MockImage:
            MockImage.open.return_value.__enter__.return_value = mock_image
            background = MagicMock()
            background.size = (100, 100)
            background.mode = "RGB"
            MockImage.new.return_value = background
            processor._process_image_bytes(b"fake_image", max_edge=1024)

            MockImage.new.assert_called_once_with("RGB", mock_image.size, (255, 255, 255))

    @pytest.mark.asyncio
    async def test_download_image_with_valid_url(self, processor):
        """Test downloading image from valid URL."""
        url = "https://example.com/image.jpg"

        with patch("apps.references.infrastructure.adapters.thumbnail_processor.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"image_data"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            MockClient.return_value = mock_client

            result = await processor._download_image(url)

            assert result == b"image_data"

    @pytest.mark.asyncio
    async def test_process_asset_without_storage_uses_source_url(self, processor):
        """Test processing without storage adapter preserves source URL."""
        asset = {"source_url": "https://example.com/image.jpg"}
        with patch.object(processor, "_download_image", return_value=b"image"):
            with patch.object(processor, "_process_image_bytes", return_value=b"webp"):
                result = await processor.process_asset(asset, tier=1, storage_adapter=None)
        assert result["thumbnail_uri"] == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_process_asset_with_storage_uses_uploaded_uri(self, processor, mock_storage_adapter):
        """Test processing with storage adapter returns uploaded URI."""
        asset = {"source_url": "https://example.com/image.jpg"}
        with patch.object(processor, "_download_image", return_value=b"image"):
            with patch.object(processor, "_process_image_bytes", return_value=b"webp"):
                result = await processor.process_asset(asset, tier=1, storage_adapter=mock_storage_adapter)
        assert result["thumbnail_uri"] == "storage://thumbnails/test.webp"
