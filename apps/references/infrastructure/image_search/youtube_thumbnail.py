"""YouTube thumbnail adapter.

YouTube Data API v3: https://www.googleapis.com/youtube/v3
License: Varies by video
Tier: 3 (high license risk - external URL only, NO video download)
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import httpx

from apps.references.application.ports import NormalizedReferenceCard
from apps.references.infrastructure.image_search.base import ImageSearchAdapter
from shared.domain.exceptions import ValidationError

logger = getLogger(__name__)


class YouTubeThumbnailAdapter(ImageSearchAdapter):
    """YouTube thumbnail adapter.

    API Documentation: https://developers.google.com/youtube/v3
    Requires: YOUTUBE_API_KEYS environment variable

    Tier: 3 (high license risk)
    - Only collects thumbnail URL metadata
    - NO video download
    - NO full image storage
    - Server-side mini-thumbnail <= 256px only (fair use)
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    TIER = 3

    def __init__(self):
        """Initialize YouTube adapter."""
        # YOUTUBE_API_KEYS can be comma-separated list for round-robin
        api_keys_str = self._get_env_key("YOUTUBE_API_KEYS")
        if not api_keys_str:
            logger.warning("YOUTUBE_API_KEYS not configured")

        super().__init__(provider_id="youtube_thumbnail", tier=self.TIER)

        self._api_keys = [key.strip() for key in api_keys_str.split(",")] if api_keys_str else []
        self._current_key_index = 0

    def is_available(self) -> bool:
        """Check if YouTube API key is configured."""
        return len(self._api_keys) > 0

    def _get_next_api_key(self) -> str | None:
        """Get next API key in round-robin fashion.

        Returns:
            API key or None if no keys available
        """
        if not self._api_keys:
            return None

        key = self._api_keys[self._current_key_index]
        self._current_key_index = (self._current_key_index + 1) % len(self._api_keys)
        return key

    async def _search_impl(
        self,
        query: str,
        count: int,
        options: dict[str, Any] | None = None,
    ) -> list[NormalizedReferenceCard]:
        """Search YouTube for videos and extract thumbnails.

        Args:
            query: Search query
            count: Number of results to return
            options: Additional options (duration, relevance, etc.)

        Returns:
            List of normalized reference cards

        Note:
            Only returns thumbnail URLs, NO video download.
            All results are tier=3 due to license variability.
        """
        if not self.is_available():
            raise ValidationError("YouTube API key not configured")

        api_key = self._get_next_api_key()
        if not api_key:
            return []

        # Build request parameters
        params = {
            "key": api_key,
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(count, 50),
        }

        # Add optional filters
        if options:
            if "duration" in options:
                params["videoDuration"] = options["duration"]
            if "order" in options:
                params["order"] = options["order"]

        try:
            response = await self._client.get(
                f"{self.BASE_URL}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Normalize results
            results = []
            items = data.get("items", [])

            for item in items:
                card = self._normalize_youtube_video(item)
                if card:
                    results.append(card)
                    if len(results) >= count:
                        break

            return results

        except httpx.HTTPStatusError as e:
            logger.error(f"YouTube API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            raise

    def _normalize_youtube_video(
        self,
        item: dict[str, Any],
    ) -> NormalizedReferenceCard | None:
        """Normalize YouTube video data to standard card format.

        Args:
            item: YouTube search result item

        Returns:
            Normalized reference card or None if invalid

        Note:
            Only extracts thumbnail URL, NO video download.
        """
        try:
            # Extract snippet
            snippet = item.get("snippet", {})

            # Extract basic info
            title = snippet.get("title")
            description = snippet.get("description")
            channel_title = snippet.get("channelTitle")

            # Extract video ID
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                return None

            # Extract thumbnail
            thumbnails = snippet.get("thumbnails", {})
            # Prefer high quality, fallback to medium
            thumbnail_data = thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default")

            if not thumbnail_data or not thumbnail_data.get("url"):
                return None

            thumbnail_url = thumbnail_data.get("url")

            # Build URLs
            external_url = f"https://www.youtube.com/watch?v={video_id}"

            # NO video download - only thumbnail URL
            # For tier 3, source_url = thumbnail_url (no full image)
            source_url = thumbnail_url

            # YouTube videos have varying licenses
            # Default to unknown (tier 3)
            license_id = "unknown"

            return NormalizedReferenceCard(
                provider="youtube_thumbnail",
                tier=self.TIER,  # Always tier 3
                external_url=external_url,
                source_url=source_url,  # Only thumbnail URL
                thumbnail_url=thumbnail_url,
                title=title,
                author=channel_title,
                license_id=license_id,
                attribution_text=f"Thumbnail © {channel_title}, YouTube",
                license_url=None,
                domain_tags=[],
                published_at=None,
                collected_at=datetime.now(timezone.utc),
                raw_meta=item,
            )

        except Exception as e:
            logger.warning(f"Failed to normalize YouTube video: {e}")
            return None
