"""Django repository implementation for concepts module."""
from typing import Optional

from apps.concepts.application.ports import ConceptRepositoryPort, DecisionRepositoryPort
from apps.concepts.domain.entities import ConceptCandidate, ConceptDecision


class DjangoConceptRepository(ConceptRepositoryPort):
    """Django ORM repository for ConceptCandidate."""

    async def save(self, concept: ConceptCandidate) -> ConceptCandidate:
        """Save a concept candidate."""
        from apps.concepts.infrastructure.orm.models import ConceptCandidateModel

        model = ConceptCandidateModel.from_domain(concept)

        # Check if it's a new concept or update
        existing = await ConceptCandidateModel.objects.filter(id=str(concept.id)).afirst()
        if existing:
            # Update existing
            model.id = existing.id
            model.save()
        else:
            # Create new
            model.save()

        return model.to_domain()

    async def get_by_id(self, concept_id):
        """Get concept by ID."""
        from apps.concepts.infrastructure.orm.models import ConceptCandidateModel

        model = await ConceptCandidateModel.objects.filter(id=str(concept_id)).afirst()
        if not model:
            return None
        return model.to_domain()

    async def list_by_session(self, session_id) -> list:
        """List all concepts for a session."""
        from apps.concepts.infrastructure.orm.models import ConceptCandidateModel

        models = ConceptCandidateModel.objects.filter(session_id=str(session_id)).order_by("-created_at")
        return [m.to_domain() async for m in models]

    async def delete(self, concept_id) -> None:
        """Delete a concept by ID."""
        from apps.concepts.infrastructure.orm.models import ConceptCandidateModel

        await ConceptCandidateModel.objects.filter(id=str(concept_id)).adelete()


class DjangoDecisionRepository(DecisionRepositoryPort):
    """Django ORM repository for ConceptDecision."""

    async def save(self, decision: ConceptDecision) -> ConceptDecision:
        """Save a concept decision."""
        from apps.concepts.infrastructure.orm.models import ConceptDecisionModel

        model = ConceptDecisionModel.from_domain(decision)
        model.save()
        return model.to_domain()

    async def list_by_concept(self, concept_id) -> list:
        """List all decisions for a concept."""
        from apps.concepts.infrastructure.orm.models import ConceptDecisionModel

        models = ConceptDecisionModel.objects.filter(concept_id=str(concept_id)).order_by("created_at")
        return [m.to_domain() async for m in models]
