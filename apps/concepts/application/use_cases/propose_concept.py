"""Use case: Propose a concept candidate."""
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.concepts.application.dtos import ConceptCandidateDTO, ProposeConceptRequest
from apps.concepts.application.ports import (
    ConceptRepositoryPort,
    DecisionRepositoryPort,
    ReferenceAnalysisPort,
    SessionPort,
    TrendInsightPort,
)
from apps.concepts.domain.entities import ConceptCandidate, ConceptStatus
from apps.concepts.domain.services import ConceptScorer


class ProposeConceptUseCase:
    """Use case for proposing a new concept candidate."""

    def __init__(
        self,
        concept_repository: ConceptRepositoryPort,
        decision_repository: DecisionRepositoryPort,
        session_port: SessionPort,
        trend_insight_port: TrendInsightPort,
        reference_analysis_port: ReferenceAnalysisPort,
        scorer: ConceptScorer,
    ):
        self.concept_repository = concept_repository
        self.decision_repository = decision_repository
        self.session_port = session_port
        self.trend_insight_port = trend_insight_port
        self.reference_analysis_port = reference_analysis_port
        self.scorer = scorer

    async def execute(self, request: ProposeConceptRequest) -> Result[ConceptCandidateDTO]:
        """Execute the use case.

        Args:
            request: ProposeConceptRequest with concept data

        Returns:
            Result with ConceptCandidateDTO on success, error on failure
        """
        try:
            # Validate session exists
            if not await self.session_port.session_exists(request.session_id):
                return Result.failure(
                    NotFoundError("DesignSession", str(request.session_id))
                )

            # Validate rationale references exist
            await self._validate_rationale_refs(request.rationale_refs)

            # Create concept entity
            concept = ConceptCandidate(
                session_id=request.session_id,
                title=request.title,
                description=request.description,
                rationale=request.rationale,
                rationale_refs=request.rationale_refs,
                domain_tags=request.domain_tags,
                status=ConceptStatus.DRAFT,
                created_by=request.created_by,
            )

            # Score the concept against brief
            brief_data = await self.session_port.get_session_brief(request.session_id)
            if brief_data:
                score = self.scorer.score_concept(
                    concept,
                    brief_keywords=brief_data.get("keywords", []),
                    brief_tone=brief_data.get("tone"),
                    brief_target_audience=brief_data.get("target_audience"),
                )
                concept.update_score(score.overall)

            # Transition to proposed status
            concept.transition_to(ConceptStatus.PROPOSED)

            # Save concept
            saved_concept = await self.concept_repository.save(concept)

            return Result.success(ConceptCandidateDTO.from_entity(saved_concept))

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("concept", f"Failed to propose concept: {str(e)}")
            )

    async def _validate_rationale_refs(self, rationale_refs: list[UUID]) -> None:
        """Validate that rationale references exist.

        Args:
            rationale_refs: List of reference IDs

        Raises:
            ValidationError: If validation fails
        """
        if len(rationale_refs) == 0:
            raise ValidationError(
                "rationale_refs",
                "At least one rationale reference (TrendInsight or ReferenceAnalysis) is required"
            )

        # Check if references are valid (at least one must exist)
        # We don't require all to be valid since we don't know the type upfront
        has_valid_refs = False

        # Try trend insights
        try:
            if await self.trend_insight_port.insights_exist(rationale_refs):
                has_valid_refs = True
        except Exception:
            pass  # Port might not be implemented yet

        # Try reference analyses
        try:
            if await self.reference_analysis_port.analyses_exist(rationale_refs):
                has_valid_refs = True
        except Exception:
            pass  # Port might not be implemented yet

        if not has_valid_refs:
            raise ValidationError(
                "rationale_refs",
                "At least one valid TrendInsight or ReferenceAnalysis reference is required"
            )
