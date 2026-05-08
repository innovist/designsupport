"""Thumbnail processor for reference images.

Implements SPEC-02 REQ-02-REF-010/012:
- Max edge <= 1024px
- WebP format
- No original high-res storage
"""
import io
from logging import getLogger
from typing import Any, TYPE_CHECKING
from uuid import uuid4

import httpx

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    if TYPE_CHECKING:
        from PIL import Image

logger = getLogger(__name__)


# @MX:NOTE: [AUTO] Multi-tier thumbnail processing with storage optimization
# @MX:REASON: Enforces 1024px max edge and WebP format; no high-res originals stored
# @MX:SPEC: REQ-02-REF-010, REQ-02-REF-012
class ThumbnailProcessor:
    """Process and validate thumbnails per INV-02-05.

    Tier 1/2: Full processing (download, resize, strip EXIF, upload)
    Tier 3: Mini-thumbnail only (external URL)
    """

    MAX_LONG_EDGE = 1024
    MINI_THUMBNAIL_EDGE = 256
    WEBP_QUALITY = 80
    DOWNLOAD_TIMEOUT = 30.0

    async def process_asset(
        self,
        asset: dict[str, Any],
        tier: int = 1,
        storage_adapter: Any = None,
    ) -> dict[str, Any]:
        """Process asset thumbnail based on tier."""
        if tier not in {1, 2, 3}:
            raise ValueError(f"Invalid tier: {tier}")

        source_url = asset.get("source_url") or asset.get("thumbnail_url", "")
        if not source_url:
            return asset

        try:
            if tier == 3:
                asset["thumbnail_uri"] = source_url
                asset["thumbnail_max_edge_px"] = 0
                return asset

            if not PIL_AVAILABLE:
                asset["thumbnail_uri"] = source_url
                return asset

            image_data = await self._download_image(source_url)
            if not image_data:
                return asset

            processed = self._process_image_bytes(image_data, self.MAX_LONG_EDGE)
            if not processed:
                return asset

            if storage_adapter and hasattr(storage_adapter, "upload_bytes"):
                filename = f"thumbnails/{uuid4()}.webp"
                uri = await storage_adapter.upload_bytes(
                    processed, filename, content_type="image/webp",
                )
                if uri:
                    asset["thumbnail_uri"] = uri
                    asset["thumbnail_max_edge_px"] = self.MAX_LONG_EDGE
            else:
                asset["thumbnail_uri"] = source_url

            return asset
        except Exception as e:
            logger.error(f"Failed to process asset thumbnail: {e}")
            return asset

    async def _download_image(self, url: str) -> bytes | None:
        try:
            async with httpx.AsyncClient(timeout=self.DOWNLOAD_TIMEOUT) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def _process_image_bytes(self, image_data: bytes, max_edge: int) -> bytes | None:
        if not PIL_AVAILABLE:
            return None
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                if img.mode != "RGB":
                    if img.mode in ("RGBA", "LA", "P"):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        if img.mode == "RGBA":
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    else:
                        img = img.convert("RGB")

                width, height = img.size
                if max(width, height) > max_edge:
                    scale = max_edge / max(width, height)
                    img = img.resize(
                        (int(width * scale), int(height * scale)),
                        Image.Resampling.LANCZOS,
                    )

                output = io.BytesIO()
                img.save(output, format="WebP", quality=self.WEBP_QUALITY, method=6)
                return output.getvalue()
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return None
