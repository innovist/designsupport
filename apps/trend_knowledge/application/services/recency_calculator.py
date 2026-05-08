"""Recency scoring service for trend insights.

Implements REQ-02-TREND-005: Old trends don't get deleted,
recency_score just decreases over time.

Pure domain service - no Django imports.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

from apps.trend_knowledge.domain.entities import TrendInsight

if TYPE_CHECKING:
    # Avoid circular import
    pass

logger = logging.getLogger(__name__)


class RecencyCalculator:
    """Calculate recency scores using exponential decay.

    Recency score starts at 1.0 for new insights and decays over time.
    Uses half-life model: score halves every half_life_days.

    Formula:
        recency_score = 0.5 ^ (age_days / half_life_days)

    Old insights are NOT deleted - their recency_score just decreases.
    Search/filter can use min_recency_score threshold.
    """

    def __init__(
        self,
        half_life_days: int = 90,
    ) -> None:
        """Initialize recency calculator.

        Args:
            half_life_days: Days for recency score to halve (default: 90)
        """
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")

        self._half_life_days = half_life_days

    def calculate(
        self,
        insight: TrendInsight,
        reference_date: datetime | None = None,
    ) -> float:
        """Calculate recency score for an insight.

        Args:
            insight: TrendInsight to score
            reference_date: Reference date for calculation (default: now)

        Returns:
            Recency score (0.0 to 1.0)
        """
        if reference_date is None:
            reference_date = datetime.now(timezone.utc)

        # Calculate age in days
        age = reference_date - insight.created_at
        age_days = age.total_seconds() / 86400.0  # Convert to days

        # Apply exponential decay
        # recency_score = 0.5 ^ (age_days / half_life_days)
        decay_factor = age_days / self._half_life_days
        recency_score = 0.5 ** decay_factor

        # Clamp to [0, 1]
        recency_score = max(0.0, min(1.0, recency_score))

        logger.debug(
            f"Insight {insight.id}: age={age_days:.1f} days, "
            f"decay_factor={decay_factor:.3f}, recency_score={recency_score:.3f}"
        )

        return recency_score

    def calculate_batch(
        self,
        insights: list[TrendInsight],
        reference_date: datetime | None = None,
    ) -> dict[str, float]:
        """Calculate recency scores for a batch of insights.

        Args:
            insights: List of TrendInsight entities
            reference_date: Reference date for calculation (default: now)

        Returns:
            Dictionary mapping insight IDs to recency scores
        """
        if reference_date is None:
            reference_date = datetime.now(timezone.utc)

        recency_scores: dict[str, float] = {}

        for insight in insights:
            score = self.calculate(insight, reference_date)
            recency_scores[str(insight.id)] = score

        return recency_scores

    def is_fresh(
        self,
        insight: TrendInsight,
        min_recency_score: float = 0.5,
        reference_date: datetime | None = None,
    ) -> bool:
        """Check if insight is still fresh (above threshold).

        Args:
            insight: TrendInsight to check
            min_recency_score: Minimum recency score threshold
            reference_date: Reference date for calculation (default: now)

        Returns:
            True if insight is fresh, False otherwise
        """
        recency_score = self.calculate(insight, reference_date)
        return recency_score >= min_recency_score

    def get_max_age_for_score(
        self,
        min_recency_score: float,
    ) -> timedelta:
        """Calculate maximum age for a given minimum recency score.

        Useful for querying insights "younger than X days".

        Args:
            min_recency_score: Minimum recency score threshold

        Returns:
            timedelta representing maximum age

        Raises:
            ValueError: If min_recency_score is not in (0, 1]
        """
        if not 0.0 < min_recency_score <= 1.0:
            raise ValueError("min_recency_score must be in (0, 1]")

        # Invert decay formula: age_days = half_life_days * log2(score)
        # score = 0.5 ^ (age / half_life)
        # log2(score) = (age / half_life) * log2(0.5) = -(age / half_life)
        # age = -half_life * log2(score)
        import math

        age_days = -self._half_life_days * (math.log2(min_recency_score))
        return timedelta(days=age_days)
