"""Use case: Decide on a concept candidate."""
from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError, StateTransitionError

from apps.concepts.application.dtos import ConceptDecisionDTO, DecideConceptRequest
from apps.concepts.application.ports import ConceptRepositoryPort, DecisionRepositoryPort
from apps.concepts.domain.entities import ConceptCandidate, ConceptDecision, ConceptStatus, DecisionType, ActorKind


class DecideConceptUseCase:
    """Use case for deciding on a concept candidate."""

    def __init__(
        self,
        concept_repository: ConceptRepositoryPort,
        decision_repository: DecisionRepositoryPort,
    ):
        self.concept_repository = concept_repository
        self.decision_repository = decision_repository

    async def execute(self, request: DecideConceptRequest) -> Result[ConceptDecisionDTO]:
        """Execute the use case.

        Args:
            request: DecideConceptRequest with decision data

        Returns:
            Result with ConceptDecisionDTO on success, error on failure
        """
        try:
            # Get concept
            concept = await self.concept_repository.get_by_id(request.concept_id)
            if not concept:
                return Result.failure(
                    NotFoundError("ConceptCandidate", str(request.concept_id))
                )

            # Parse decision type
            try:
                decision_type = DecisionType(request.decision)
            except ValueError:
                return Result.failure(
                    ValidationError("decision", f"Invalid decision type: {request.decision}")
                )

            # Parse actor kind
            try:
                actor_kind = ActorKind(request.actor_kind)
            except ValueError:
                return Result.failure(
                    ValidationError("actor_kind", f"Invalid actor kind: {request.actor_kind}")
                )

            # Update concept status based on decision
            new_status = self._map_decision_to_status(decision_type)
            try:
                concept.transition_to(new_status)
            except StateTransitionError as e:
                return Result.failure(e)

            # Create decision record
            decision = ConceptDecision(
                concept_id=request.concept_id,
                decision=decision_type,
                actor_kind=actor_kind,
                actor_id=request.actor_id,
                rationale=request.rationale,
            )

            # Save both
            await self.concept_repository.save(concept)
            saved_decision = await self.decision_repository.save(decision)

            return Result.success(ConceptDecisionDTO.from_entity(saved_decision))

        except (ValidationError, StateTransitionError) as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("decision", f"Failed to record decision: {str(e)}")
            )

    def _map_decision_to_status(self, decision: DecisionType) -> ConceptStatus:
        """Map decision type to concept status.

        Args:
            decision: Decision type

        Returns:
            Corresponding ConceptStatus
        """
        mapping = {
            DecisionType.ADOPT: ConceptStatus.ADOPTED,
            DecisionType.HOLD: ConceptStatus.PROPOSED,
            DecisionType.DISCARD: ConceptStatus.DISCARDED,
            DecisionType.EXPLORE_MORE: ConceptStatus.PROPOSED,
        }
        return mapping.get(decision, ConceptStatus.PROPOSED)
