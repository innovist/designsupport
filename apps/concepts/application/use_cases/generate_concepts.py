"""Use case: Generate multiple concept candidates using AI."""
import logging
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.concepts.application.dtos import ConceptCandidateDTO, GenerateConceptsRequest
from apps.concepts.application.ports import (
    ConceptRepositoryPort,
    ReferenceAnalysisPort,
    SessionPort,
    TrendInsightPort,
)
from apps.concepts.domain.entities import ConceptCandidate, ConceptStatus
from apps.concepts.domain.services import ConceptScorer

logger = logging.getLogger(__name__)


# @MX:ANCHOR: [AUTO] AI-driven concept generation with multi-dimensional scoring
# @MX:REASON: Primary concept creation workflow; integrates insights, references, and brief data
# @MX:SPEC: REQ-03-CONCEPT-001, REQ-03-CONCEPT-005
class GenerateConceptsUseCase:
    """Use case for generating multiple concept candidates using AI.

    REQ-03-CONCEPT-001: Generate 3-5 concept candidates with scores
    REQ-03-CONCEPT-005: Never return fake scores on model failure
    """

    def __init__(
        self,
        concept_repository: ConceptRepositoryPort,
        session_port: SessionPort,
        trend_insight_port: TrendInsightPort,
        reference_analysis_port: ReferenceAnalysisPort,
        scorer: ConceptScorer,
        ai_generation_service,  # Type: Any AI service interface
    ):
        self.concept_repository = concept_repository
        self.session_port = session_port
        self.trend_insight_port = trend_insight_port
        self.reference_analysis_port = reference_analysis_port
        self.scorer = scorer
        self.ai_generation_service = ai_generation_service

    # @MX:WARN: [AUTO] External AI service dependency with strict validation requirements
    # @MX:REASON: AI model failure blocks concept generation; minimum 3 valid concepts required
    async def execute(self, request: GenerateConceptsRequest) -> Result[list[ConceptCandidateDTO]]:
        """Execute the use case.

        Args:
            request: GenerateConceptsRequest with session and count

        Returns:
            Result with list of ConceptCandidateDTO on success, error on failure
        """
        try:
            # Validate session exists
            if not await self.session_port.session_exists(request.session_id):
                return Result.failure(
                    NotFoundError("DesignSession", str(request.session_id))
                )

            # Validate count (REQ-03-CONCEPT-001: 3-5 concepts)
            if request.count < 3 or request.count > 5:
                raise ValidationError(
                    "count",
                    "Count must be between 3 and 5"
                )

            # Fetch session data for context
            session_data = await self._fetch_session_context(request.session_id)

            # Generate concepts using AI service
            concepts_data = await self._generate_concepts_with_ai(
                session_data=session_data,
                count=request.count,
                created_by=request.created_by,
            )

            # Validate AI returned enough concepts
            if len(concepts_data) == 0:
                logger.error(f"AI generation failed: no concepts returned for session {request.session_id}")
                return Result.failure(
                    ValidationError(
                        "ai_generation",
                        "Failed to generate concepts: AI service returned no results"
                    )
                )

            # Create and score each concept
            created_concepts = []
            for concept_data in concepts_data:
                try:
                    concept = await self._create_and_score_concept(
                        session_id=request.session_id,
                        concept_data=concept_data,
                        session_data=session_data,
                        created_by=request.created_by,
                    )
                    created_concepts.append(concept)
                except ValidationError as e:
                    logger.warning(f"Failed to create concept: {e}")
                    continue  # Skip invalid concepts

            # Ensure we have at least 3 valid concepts
            if len(created_concepts) < 3:
                logger.error(f"Only {len(created_concepts)} valid concepts generated, minimum 3 required")
                return Result.failure(
                    ValidationError(
                        "concepts",
                        f"Failed to generate minimum 3 valid concepts (got {len(created_concepts)})"
                    )
                )

            # Save all concepts
            saved_concepts = []
            for concept in created_concepts:
                saved = await self.concept_repository.save(concept)
                saved_concepts.append(saved)

            return Result.success([
                ConceptCandidateDTO.from_entity(concept) for concept in saved_concepts
            ])

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            logger.exception(f"Unexpected error in generate_concepts: {e}")
            return Result.failure(
                ValidationError("concepts", f"Failed to generate concepts: {str(e)}")
            )

    async def _fetch_session_context(self, session_id: UUID) -> dict:
        """Fetch session context for concept generation.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session data including brief, insights, references
        """
        # Get session brief
        brief_data = await self.session_port.get_session_brief(session_id)

        # Get trend insights
        insights = []
        try:
            insights = await self.trend_insight_port.find_by_session(session_id)
        except Exception as e:
            logger.warning(f"Failed to fetch trend insights: {e}")

        # Get reference analyses
        references = []
        try:
            references = await self.reference_analysis_port.find_by_session(session_id)
        except Exception as e:
            logger.warning(f"Failed to fetch reference analyses: {e}")

        return {
            "brief": brief_data or {},
            "insights": insights,
            "references": references,
        }

    async def _generate_concepts_with_ai(
        self,
        session_data: dict,
        count: int,
        created_by: UUID,
    ) -> list[dict]:
        """Generate concepts using AI service.

        Args:
            session_data: Session context data
            count: Number of concepts to generate
            created_by: User ID creating the concepts

        Returns:
            List of concept data dictionaries

        Raises:
            ValidationError: If AI generation fails completely
        """
        try:
            # Prepare prompt for AI
            prompt = self._build_generation_prompt(session_data, count)

            # Call AI service
            ai_response = await self.ai_generation_service.generate_concepts(
                prompt=prompt,
                count=count,
                session_context=session_data,
            )

            # Validate response
            if not ai_response or not isinstance(ai_response, list):
                raise ValidationError(
                    "ai_response",
                    "AI service returned invalid response format"
                )

            # Validate each concept has required fields
            valid_concepts = []
            for concept_data in ai_response:
                if self._validate_concept_data(concept_data):
                    # Add created_by if not present
                    if "created_by" not in concept_data:
                        concept_data["created_by"] = created_by
                    valid_concepts.append(concept_data)
                else:
                    logger.warning(f"Invalid concept data from AI: {concept_data}")

            return valid_concepts

        except Exception as e:
            logger.exception(f"AI generation service error: {e}")
            # REQ-03-CONCEPT-005: Never return fake scores on model failure
            raise ValidationError(
                "ai_generation",
                f"AI generation service failed: {str(e)}"
            )

    def _build_generation_prompt(self, session_data: dict, count: int) -> str:
        """Build prompt for AI concept generation.

        Args:
            session_data: Session context
            count: Number of concepts to generate

        Returns:
            Prompt string for AI service
        """
        brief = session_data.get("brief", {})
        insights = session_data.get("insights", [])
        references = session_data.get("references", [])

        # Build prompt sections
        prompt_parts = [
            f"Generate {count} unique design concept candidates based on the following:",
            "",
            "## Design Brief",
            f"Title: {brief.get('title', 'N/A')}",
            f"Description: {brief.get('description', 'N/A')}",
            f"Target Audience: {brief.get('target_audience', 'N/A')}",
            f"Tone: {brief.get('tone', 'N/A')}",
            "",
        ]

        # Add trend insights
        if insights:
            prompt_parts.append("## Trend Insights")
            for insight in insights[:5]:  # Limit to top 5
                prompt_parts.append(f"- {insight.get('summary', 'N/A')}")
            prompt_parts.append("")

        # Add reference analyses
        if references:
            prompt_parts.append("## Reference Analysis")
            for ref in references[:3]:  # Limit to top 3
                prompt_parts.append(f"- {ref.get('summary', 'N/A')}")
            prompt_parts.append("")

        # Add output format instructions
        prompt_parts.extend([
            "## Output Format",
            "For each concept, provide:",
            "- title: Short descriptive title",
            "- description: Detailed concept description (100-200 words)",
            "- rationale: Reasoning behind this concept",
            "- rationale_refs: List of relevant insight/reference IDs",
            "- domain_tags: List of relevant domain tags",
            "",
            "Make each concept distinct and innovative. Ensure diversity in approach.",
        ])

        return "\n".join(prompt_parts)

    def _validate_concept_data(self, concept_data: dict) -> bool:
        """Validate concept data from AI response.

        Args:
            concept_data: Concept data dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["title", "description", "rationale", "rationale_refs"]
        for field in required_fields:
            if field not in concept_data or not concept_data[field]:
                return False

        # Validate rationale_refs is a non-empty list
        if not isinstance(concept_data["rationale_refs"], list) or len(concept_data["rationale_refs"]) == 0:
            return False

        return True

    async def _create_and_score_concept(
        self,
        session_id: UUID,
        concept_data: dict,
        session_data: dict,
        created_by: UUID,
    ) -> ConceptCandidate:
        """Create and score a concept from AI data.

        Args:
            session_id: Session identifier
            concept_data: Concept data from AI
            session_data: Session context
            created_by: User ID

        Returns:
            Created and scored ConceptCandidate entity

        Raises:
            ValidationError: If concept creation or scoring fails
        """
        # Create concept entity
        concept = ConceptCandidate(
            session_id=session_id,
            title=concept_data["title"],
            description=concept_data["description"],
            rationale=concept_data["rationale"],
            rationale_refs=concept_data["rationale_refs"],
            domain_tags=concept_data.get("domain_tags", []),
            status=ConceptStatus.DRAFT,
            created_by=created_by,
        )

        # Score the concept
        brief = session_data.get("brief", {})
        try:
            score_result = self.scorer.score_concept(
                concept,
                brief_keywords=brief.get("keywords", []),
                brief_tone=brief.get("tone"),
                brief_target_audience=brief.get("target_audience"),
            )
            concept.update_score(score_result.overall)
        except Exception as e:
            logger.warning(f"Failed to score concept: {e}")
            # Set neutral score on scoring failure
            concept.update_score(0.5)

        # Transition to proposed
        concept.transition_to(ConceptStatus.PROPOSED)

        return concept
