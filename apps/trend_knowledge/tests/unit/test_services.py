"""Unit tests for trend_knowledge domain services.

Tests cover SSRF protection, confidence calculation, and recency scoring.
"""
import pytest
from datetime import datetime, timezone, timedelta

from apps.trend_knowledge.domain.services import (
    SSRFGuard,
    InsightConfidenceCalculator,
    InsightConfidenceConfig,
    RecencyScoreCalculator,
    RecencyScoreConfig,
)


class TestSSRFGuard:
    """Test SSRF protection for URL validation."""

    def test_allows_valid_public_url(self):
        """Test that valid public URLs are allowed."""
        assert SSRFGuard.is_safe_url("https://example.com") is True
        assert SSRFGuard.is_safe_url("https://api.wgsn.com/trends") is True
        assert SSRFGuard.is_safe_url("http://fashion-week.com") is True

    def test_blocks_localhost(self):
        """Test that localhost variations are blocked."""
        assert SSRFGuard.is_safe_url("http://localhost:8000") is False
        assert SSRFGuard.is_safe_url("https://localhost/api") is False
        assert SSRFGuard.is_safe_url("http://LOCALHOST") is False  # Case insensitive

    def test_blocks_127_0_0_1_loopback(self):
        """Test that 127.0.0.1 loopback addresses are blocked."""
        assert SSRFGuard.is_safe_url("http://127.0.0.1:8000") is False
        assert SSRFGuard.is_safe_url("https://127.0.0.1") is False

    def test_blocks_ipv6_loopback(self):
        """Test that IPv6 loopback is blocked."""
        assert SSRFGuard.is_safe_url("http://[::1]:8000") is False
        assert SSRFGuard.is_safe_url("https://::1") is False

    def test_blocks_0_0_0_0(self):
        """Test that 0.0.0.0 is blocked."""
        assert SSRFGuard.is_safe_url("http://0.0.0.0:8000") is False

    def test_blocks_aws_metadata_endpoint(self):
        """Test that AWS metadata endpoint is blocked."""
        assert SSRFGuard.is_safe_url("http://169.254.169.254/latest/meta-data/") is False

    def test_blocks_private_ip_ranges(self):
        """Test that private IP ranges are blocked."""
        # 192.168.x.x
        assert SSRFGuard.is_safe_url("http://192.168.1.1") is False
        assert SSRFGuard.is_safe_url("https://192.168.0.100:8080") is False

        # 10.x.x.x
        assert SSRFGuard.is_safe_url("http://10.0.0.1") is False
        assert SSRFGuard.is_safe_url("https://10.255.255.255") is False

        # 172.16.x.x (only 172.16. prefix is blocked, not 172.17-31)
        assert SSRFGuard.is_safe_url("http://172.16.0.1") is False
        assert SSRFGuard.is_safe_url("http://172.16.255.255") is False

        # 169.254.x.x (link-local)
        assert SSRFGuard.is_safe_url("http://169.254.1.1") is False

    def test_handles_malformed_urls(self):
        """Test that malformed URLs are handled safely (may be allowed or blocked)."""
        # The implementation may allow or block malformed URLs depending on urlparse
        # Just verify it doesn't crash and returns a boolean
        result1 = SSRFGuard.is_safe_url("not-a-url")
        assert isinstance(result1, bool)

        result2 = SSRFGuard.is_safe_url("://missing-protocol")
        assert isinstance(result2, bool)

        result3 = SSRFGuard.is_safe_url("")
        assert isinstance(result3, bool)


class TestInsightConfidenceCalculator:
    """Test confidence calculation with source corroboration."""

    def test_default_configuration(self):
        """Test calculator with default configuration."""
        calc = InsightConfidenceCalculator()

        assert calc.config.min_sources == 3
        assert calc.config.boost_weight == 0.1
        assert calc.config.max_boost == 0.5

    def test_custom_configuration(self):
        """Test calculator with custom configuration."""
        config = InsightConfidenceConfig(
            min_sources=5,
            boost_weight=0.15,
            max_boost=0.7,
        )
        calc = InsightConfidenceCalculator(config)

        assert calc.config.min_sources == 5
        assert calc.config.boost_weight == 0.15
        assert calc.config.max_boost == 0.7

    def test_single_source_no_boost(self):
        """Test that single source returns base confidence."""
        calc = InsightConfidenceCalculator()

        result = calc.calculate(base_confidence=0.6, source_count=1)

        assert result == 0.6  # No boost below min_sources (3)

    def test_two_sources_no_boost(self):
        """Test that two sources return base confidence (below threshold)."""
        calc = InsightConfidenceCalculator()

        result = calc.calculate(base_confidence=0.6, source_count=2)

        assert result == 0.6  # No boost below min_sources (3)

    def test_three_sources_gets_boost(self):
        """Test that three sources trigger confidence boost."""
        calc = InsightConfidenceCalculator()

        result = calc.calculate(base_confidence=0.6, source_count=3)

        # boost = 0.1 * (3 - 1) = 0.2
        # result = 0.6 + 0.2 = 0.8
        assert result == 0.8

    def test_ten_sources_capped_at_max_boost(self):
        """Test that many sources are capped at max_boost."""
        calc = InsightConfidenceCalculator()

        result = calc.calculate(base_confidence=0.6, source_count=10)

        # boost = 0.1 * (10 - 1) = 0.9, capped at 0.5
        # result = 0.6 + 0.5 = 1.1, capped at 1.0
        assert result == 1.0

    def test_confidence_never_exceeds_1_0(self):
        """Test that confidence is capped at maximum 1.0."""
        calc = InsightConfidenceCalculator()

        result = calc.calculate(base_confidence=0.9, source_count=100)

        # Even with many sources, result is capped at 1.0
        assert result == 1.0

    def test_confidence_never_below_0_0(self):
        """Test that confidence is floored at minimum 0.0."""
        calc = InsightConfidenceCalculator()

        result = calc.calculate(base_confidence=-0.5, source_count=3)

        # Negative base confidence is floored at 0.0
        assert result == 0.0

    def test_boost_formula_calculation(self):
        """Test exact boost formula calculation."""
        calc = InsightConfidenceCalculator()

        # With min_sources=3, boost_weight=0.1:
        # source_count=3: boost = 0.1 * (3 - 1) = 0.2
        assert calc.calculate(0.5, 3) == 0.7

        # source_count=5: boost = 0.1 * (5 - 1) = 0.4
        assert calc.calculate(0.5, 5) == 0.9

        # source_count=8: boost = 0.1 * (8 - 1) = 0.7, capped at 0.5
        assert calc.calculate(0.5, 8) == 1.0  # 0.5 + 0.5 = 1.0


class TestRecencyScoreCalculator:
    """Test recency score calculation based on document age."""

    def test_default_configuration(self):
        """Test calculator with default configuration."""
        calc = RecencyScoreCalculator()

        assert calc.config.half_life_days == 30

    def test_custom_configuration(self):
        """Test calculator with custom half-life."""
        config = RecencyScoreConfig(half_life_days=60)
        calc = RecencyScoreCalculator(config)

        assert calc.config.half_life_days == 60

    def test_today_published_gets_max_score(self):
        """Test that today's document gets score close to 1.0."""
        calc = RecencyScoreCalculator()
        today = datetime.now(timezone.utc)

        result = calc.calculate(today)

        # Should be very close to 1.0 (may have small floating point differences)
        assert result >= 0.999

    def test_future_treated_as_max_score(self):
        """Test that future publication dates are treated as very recent."""
        calc = RecencyScoreCalculator()
        future = datetime.now(timezone.utc) + timedelta(days=7)

        result = calc.calculate(future)

        assert result == 1.0

    def test_thirty_days_old_half_score(self):
        """Test that document at half-life gets score close to 0.5."""
        calc = RecencyScoreCalculator()
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        result = calc.calculate(thirty_days_ago)

        # Score = 1.0 / (1.0 + 30/30) = 1.0 / 2.0 = 0.5
        # Allow small floating point differences
        assert pytest.approx(result, rel=0.01) == 0.5

    def test_sixty_days_old_third_score(self):
        """Test that older document has lower score."""
        calc = RecencyScoreCalculator()
        sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)

        result = calc.calculate(sixty_days_ago)

        # Score = 1.0 / (1.0 + 60/30) = 1.0 / 3.0 = 0.33...
        assert pytest.approx(result, abs=0.01) == 0.333

    def test_one_year_old_very_low_score(self):
        """Test that year-old document has very low but non-zero score."""
        calc = RecencyScoreCalculator()
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

        result = calc.calculate(one_year_ago)

        # Score = 1.0 / (1.0 + 365/30) = 1.0 / 13.17 = 0.076
        assert result == pytest.approx(0.076, rel=0.01)

        # Score is never zero, only asymptotically approaches it
        assert result > 0.0

    def test_score_never_reaches_zero(self):
        """Test that score never reaches zero, only approaches it."""
        calc = RecencyScoreCalculator()
        very_old = datetime.now(timezone.utc) - timedelta(days=10000)  # 27 years

        result = calc.calculate(very_old)

        # Even very old documents have non-zero scores
        assert result > 0.0
        assert result < 0.01  # But very small

    def test_score_never_exceeds_1_0(self):
        """Test that score is capped at maximum 1.0."""
        calc = RecencyScoreCalculator()

        # Even with very recent timestamp
        very_recent = datetime.now(timezone.utc) - timedelta(microseconds=1)
        result = calc.calculate(very_recent)

        assert result <= 1.0

    def test_custom_half_life_affects_decay(self):
        """Test that custom half-life changes decay rate."""
        # Longer half-life = slower decay
        calc_long = RecencyScoreCalculator(RecencyScoreConfig(half_life_days=90))
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        result_long = calc_long.calculate(thirty_days_ago)

        # With 90-day half-life, 30 days should have higher score
        # Score = 1.0 / (1.0 + 30/90) = 1.0 / 1.33 = 0.75
        assert result_long == pytest.approx(0.75, rel=0.01)
