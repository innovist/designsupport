"""Trend Knowledge domain services.

Business logic services that operate on domain entities.
M and weight are from config, not hardcoded.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


def _utcnow() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass
class InsightConfidenceConfig:
    """Configuration for confidence calculation.

    Attributes:
        min_sources: Minimum number of sources (M) required for confidence boost
        boost_weight: Weight for confidence boost per additional source
        max_boost: Maximum confidence boost cap
    """

    min_sources: int = 3
    boost_weight: float = 0.1
    max_boost: float = 0.5


# @MX:ANCHOR: [AUTO] Core confidence calculation with multi-source corroboration
# @MX:REASON: High fan-in function used across insight scoring and RAG pipeline
class InsightConfidenceCalculator:
    """Calculate confidence for insights based on source corroboration.

    When multiple sources report the same claim, confidence increases monotonically.
    Formula: base + min(boost_weight * (n_sources - 1), max_boost)

    This is data-driven - M and weight come from config, not hardcoded.
    """

    def __init__(self, config: Optional[InsightConfidenceConfig] = None):
        """Initialize calculator with configuration."""
        self.config = config or InsightConfidenceConfig()

    def calculate(
        self,
        base_confidence: float,
        source_count: int,
    ) -> float:
        """Calculate confidence with source corroboration boost.

        Args:
            base_confidence: Single-source confidence (0.0 to 1.0)
            source_count: Number of sources reporting the same claim

        Returns:
            Adjusted confidence score (0.0 to 1.0)

        Example:
            With M=3, weight=0.1, max_boost=0.5:
            - 1 source: 0.6 + 0.0 = 0.6
            - 2 sources: 0.6 + 0.0 = 0.6 (below M)
            - 3 sources: 0.6 + min(0.1 * 2, 0.5) = 0.6 + 0.2 = 0.8
            - 10 sources: 0.6 + min(0.1 * 9, 0.5) = 0.6 + 0.5 = 1.0 (capped)
        """
        if source_count < self.config.min_sources:
            return base_confidence

        boost = self.config.boost_weight * (source_count - 1)
        capped_boost = min(boost, self.config.max_boost)
        adjusted = base_confidence + capped_boost

        return min(1.0, max(0.0, adjusted))


@dataclass
class RecencyScoreConfig:
    """Configuration for recency score calculation.

    Attributes:
        half_life_days: Half-life in days for score decay
    """

    half_life_days: int = 30


# @MX:NOTE: [AUTO] Time-decay formula ensures old insights never reach zero score
# @MX:REASON: Asymptotic decay preserves historical data while prioritizing recency
class RecencyScoreCalculator:
    """Calculate recency score for trend insights.

    Score decreases with age but never reaches zero.
    Formula: 1.0 / (1.0 + age_days / half_life_days)

    This ensures old insights are preserved but weighted lower.
    """

    def __init__(self, config: Optional[RecencyScoreConfig] = None):
        """Initialize calculator with configuration."""
        self.config = config or RecencyScoreConfig()

    def calculate(self, published_at: datetime) -> float:
        """Calculate recency score based on publication date.

        Args:
            published_at: Original publication timestamp

        Returns:
            Recency score (0.0 to 1.0)

        Examples with half_life_days=30:
        - Published today: 1.0 / (1.0 + 0/30) = 1.0
        - Published 30 days ago: 1.0 / (1.0 + 30/30) = 0.5
        - Published 60 days ago: 1.0 / (1.0 + 60/30) = 0.33
        - Published 1 year ago: 1.0 / (1.0 + 365/30) = 0.076

        The score never reaches zero, only asymptotically approaches it.
        """
        now = _utcnow()
        age_days = (now - published_at).total_seconds() / 86400.0

        if age_days < 0:
            # Future publication date - treat as very recent
            return 1.0

        score = 1.0 / (1.0 + age_days / self.config.half_life_days)
        return max(0.0, min(1.0, score))


# @MX:WARN: [AUTO] SSRF protection prevents internal network access
# @MX:REASON: Blocks localhost/private IPs to prevent Server-Side Request Forgery
class SSRFGuard:
    """Guard against Server-Side Request Forgery (SSRF) attacks.

    Validates that URLs are safe to access from the server.
    """

    # Blocked private/network ranges
    BLOCKED_HOSTS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "169.254.169.254",  # AWS metadata
    }

    BLOCKED_PATTERNS = {
        "192.168.",
        "10.",
        "172.16.",
        "169.254.",
    }

    @classmethod
    def is_safe_url(cls, url: str) -> bool:
        """Check if a URL is safe to access.

        Args:
            url: URL to validate

        Returns:
            True if safe, False if blocked
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or parsed.netloc

            # Check blocked hosts
            if hostname.lower() in cls.BLOCKED_HOSTS:
                return False

            # Check blocked patterns
            for pattern in cls.BLOCKED_PATTERNS:
                if hostname.startswith(pattern):
                    return False

            return True
        except Exception:
            # If parsing fails, block the URL
            return False
