"""Confidence calculation service for trend insights.

Implements REQ-02-TREND-004: When M sources repeat same claim,
confidence increases monotonically.

Pure domain service - no Django imports.
"""
import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from apps.trend_knowledge.domain.entities import TrendInsight

if TYPE_CHECKING:
    # Avoid circular import
    pass

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Calculate confidence scores based on source overlap.

    When M sources repeat similar claims, confidence increases.
    M and boost amount are configurable.

    Algorithm:
    1. Group insights by semantic similarity (simplified via keyword overlap)
    2. Count how many unique sources support each claim cluster
    3. Apply boost for each source beyond threshold M
    """

    def __init__(
        self,
        min_sources_threshold: int = 3,
        boost_per_additional_source: float = 0.1,
        keyword_match_threshold: int = 2,
    ) -> None:
        """Initialize confidence calculator.

        Args:
            min_sources_threshold: Minimum number of sources (M) before boost applies
            boost_per_additional_source: Confidence boost per additional source
            keyword_match_threshold: Minimum keyword overlaps to consider claims similar
        """
        self._min_sources_threshold = min_sources_threshold
        self._boost_per_additional_source = boost_per_additional_source
        self._keyword_match_threshold = keyword_match_threshold

    def calculate_batch(
        self,
        insights: list[TrendInsight],
    ) -> dict[str, float]:
        """Calculate confidence scores for a batch of insights.

        Recalculates confidence based on source overlap across all insights.
        Returns mapping of insight_id -> updated_confidence.

        Args:
            insights: List of TrendInsight entities

        Returns:
            Dictionary mapping insight IDs to recalculated confidence scores
        """
        if not insights:
            return {}

        # Group insights by claim similarity (via keyword overlap)
        claim_clusters = self._cluster_similar_claims(insights)

        # Calculate confidence for each cluster
        confidence_updates: dict[str, float] = {}

        for cluster_id, cluster_insights in claim_clusters.items():
            # Count unique sources (document_ids)
            unique_sources = set(insight.document_id for insight in cluster_insights)
            source_count = len(unique_sources)

            # Calculate boost based on source count
            if source_count >= self._min_sources_threshold:
                additional_sources = source_count - self._min_sources_threshold
                boost = additional_sources * self._boost_per_additional_source
            else:
                boost = 0.0

            # Apply boost to each insight in cluster
            for insight in cluster_insights:
                # Boost is additive to existing confidence, capped at 1.0
                updated_confidence = min(1.0, insight.confidence + boost)
                confidence_updates[str(insight.id)] = updated_confidence

                logger.debug(
                    f"Insight {insight.id}: {source_count} sources, "
                    f"boost={boost:.3f}, confidence={insight.confidence:.3f} -> {updated_confidence:.3f}"
                )

        return confidence_updates

    def calculate_single(
        self,
        insight: TrendInsight,
        all_insights: list[TrendInsight] | None = None,
    ) -> float:
        """Calculate confidence for a single insight.

        If all_insights is provided, considers source overlap.
        Otherwise, returns the insight's base confidence.

        Args:
            insight: The insight to calculate confidence for
            all_insights: Optional list of all insights for source overlap analysis

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if all_insights is None:
            # No source overlap analysis available
            return insight.confidence

        # Find cluster containing this insight
        claim_clusters = self._cluster_similar_claims(all_insights)

        for cluster_insights in claim_clusters.values():
            if any(i.id == insight.id for i in cluster_insights):
                # Found the cluster - calculate confidence
                unique_sources = set(i.document_id for i in cluster_insights)
                source_count = len(unique_sources)

                if source_count >= self._min_sources_threshold:
                    additional_sources = source_count - self._min_sources_threshold
                    boost = additional_sources * self._boost_per_additional_source
                else:
                    boost = 0.0

                return min(1.0, insight.confidence + boost)

        # Insight not found in any cluster (shouldn't happen)
        return insight.confidence

    def _cluster_similar_claims(
        self,
        insights: list[TrendInsight],
    ) -> dict[int, list[TrendInsight]]:
        """Cluster insights by claim similarity using keyword overlap.

        Simple implementation: group insights with overlapping keywords.
        Production system would use embeddings or semantic similarity.

        Args:
            insights: List of insights to cluster

        Returns:
            Dictionary mapping cluster_id to list of insights in that cluster
        """
        clusters: dict[int, list[TrendInsight]] = defaultdict(list)
        cluster_counter = 0
        assigned_insights = set()

        for insight in insights:
            if insight.id in assigned_insights:
                continue

            # Start new cluster
            current_cluster = [insight]
            assigned_insights.add(insight.id)
            insight_keywords = set(insight.keywords)

            # Find similar insights
            for other_insight in insights:
                if other_insight.id in assigned_insights:
                    continue

                # Check keyword overlap
                other_keywords = set(other_insight.keywords)
                overlap = len(insight_keywords & other_keywords)

                if overlap >= self._keyword_match_threshold:
                    current_cluster.append(other_insight)
                    assigned_insights.add(other_insight.id)
                    insight_keywords.update(other_keywords)

            clusters[cluster_counter] = current_cluster
            cluster_counter += 1

        return dict(clusters)
