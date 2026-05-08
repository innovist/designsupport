"""Domain services for concepts module.

This file is pure Python - no Django imports allowed.
"""
from typing import Optional

from shared.domain.exceptions import ValidationError

from apps.concepts.domain.entities import ConceptCandidate
from apps.concepts.domain.value_objects import ConceptScore


class ConceptValidator:
    """Service for validating concept candidates."""

    @staticmethod
    def validate_rationale_refs(rationale_refs: list, has_insights: bool, has_references: bool) -> None:
        """Validate that rationale_refs has at least 1 TrendInsight or ReferenceAnalysis.

        Args:
            rationale_refs: List of reference IDs
            has_insights: Whether TrendInsight references exist
            has_references: Whether ReferenceAnalysis references exist

        Raises:
            ValidationError: If validation fails
        """
        if len(rationale_refs) == 0:
            raise ValidationError(
                "rationale_refs",
                "At least one rationale reference (TrendInsight or ReferenceAnalysis) is required"
            )

        if not has_insights and not has_references:
            raise ValidationError(
                "rationale_refs",
                "Concept must reference at least one TrendInsight or ReferenceAnalysis"
            )


# @MX:ANCHOR: [AUTO] Multi-dimensional concept scoring against design brief
# @MX:REASON: Core scoring logic used by concept generation and evaluation workflows
class ConceptScorer:
    """Service for scoring concept candidates against brief criteria."""

    # @MX:TODO: [AUTO] Missing integration test for multi-dimensional scoring
    # @MX:REASON: Simplified implementation needs production validation with AI model calls
    def score_concept(
        self,
        concept: ConceptCandidate,
        brief_keywords: list[str],
        brief_tone: Optional[str] = None,
        brief_target_audience: Optional[str] = None
    ) -> ConceptScore:
        """Score a concept against brief criteria.

        Args:
            concept: The concept to score
            brief_keywords: Keywords from the design brief
            brief_tone: Optional tone from brief
            brief_target_audience: Optional target audience from brief

        Returns:
            ConceptScore with fit_score, novelty, feasibility, and overall

        Note:
            This is a simplified scoring implementation. In production, this would
            use AI model calls to analyze the concept against the brief.
        """
        # Calculate fit score based on keyword matching
        fit_score = self._calculate_fit_score(concept, brief_keywords, brief_tone, brief_target_audience)

        # Calculate novelty based on domain tags uniqueness
        novelty = self._calculate_novelty(concept)

        # Calculate feasibility based on description complexity
        feasibility = self._calculate_feasibility(concept)

        # Calculate overall score
        return ConceptScore.calculate(
            fit_score=fit_score,
            novelty=novelty,
            feasibility=feasibility
        )

    def _calculate_fit_score(
        self,
        concept: ConceptCandidate,
        keywords: list[str],
        tone: Optional[str],
        target_audience: Optional[str]
    ) -> float:
        """Calculate how well the concept fits the brief."""
        if not keywords:
            return 0.5  # Neutral score if no keywords

        concept_text = f"{concept.title} {concept.description} {concept.rationale}".lower()
        keyword_matches = sum(1 for kw in keywords if kw.lower() in concept_text)

        # Base score from keyword matches
        base_score = min(keyword_matches / len(keywords), 1.0)

        # Boost score if tone matches (if specified)
        if tone and tone.lower() in concept_text:
            base_score = min(base_score + 0.1, 1.0)

        # Boost score if target audience matches (if specified)
        if target_audience and target_audience.lower() in concept_text:
            base_score = min(base_score + 0.1, 1.0)

        return base_score

    def _calculate_novelty(self, concept: ConceptCandidate) -> float:
        """Calculate how novel/innovative the concept is."""
        # Simplified implementation based on domain tag diversity
        if not concept.domain_tags:
            return 0.5

        # More unique tags = higher novelty
        unique_tags = len(set(concept.domain_tags))
        return min(unique_tags / 10.0, 1.0)  # Cap at 10 unique tags

    def _calculate_feasibility(self, concept: ConceptCandidate) -> float:
        """Calculate how feasible the concept is to implement."""
        # Simplified implementation based on description complexity
        word_count = len(concept.description.split())

        # Very short descriptions might lack detail
        if word_count < 20:
            return 0.4

        # Very long descriptions might be too complex
        if word_count > 500:
            return 0.6

        # Sweet spot: detailed but not overwhelming
        return 0.8
