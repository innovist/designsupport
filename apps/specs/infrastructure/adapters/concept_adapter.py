"""Django ORM adapter for Concept port.

Implements ConceptPort from concepts module.
"""
from uuid import UUID
from typing import Optional

from apps.specs.application.ports import ConceptPort


class DjangoORMConceptAdapter(ConceptPort):
    """Django ORM adapter for accessing concept candidates."""

    async def get_concepts_by_session(self, session_id: UUID) -> list[dict]:
        """Get all concepts for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of concept data including decisions
        """
        from apps.concepts.infrastructure.orm.models import ConceptCandidateModel

        concepts = ConceptCandidateModel.objects.filter(session_id=str(session_id)).order_by("-created_at")
        return [
            {
                "id": str(concept.id),
                "session_id": str(concept.session_id),
                "title": concept.title,
                "description": concept.description,
                "rationale": concept.rationale,
                "status": concept.status,
                "score": concept.score,
                "novelty": concept.novelty,
                "fit_score": concept.fit_score,
                "domain_tags": concept.domain_tags,
                "risks": concept.risks,
                "created_by": str(concept.created_by),
                "created_at": concept.created_at.isoformat(),
            }
            async for concept in concepts
        ]

    async def get_adopted_concept(self, session_id: UUID) -> Optional[dict]:
        """Get the adopted concept for a session.

        Args:
            session_id: Session UUID

        Returns:
            Adopted concept data if found, None otherwise
        """
        from apps.concepts.infrastructure.orm.models import ConceptCandidateModel

        try:
            concept = await ConceptCandidateModel.objects.aget(
                session_id=str(session_id), status="adopted"
            )
            return {
                "id": str(concept.id),
                "session_id": str(concept.session_id),
                "title": concept.title,
                "description": concept.description,
                "rationale": concept.rationale,
                "status": concept.status,
                "score": concept.score,
                "novelty": concept.novelty,
                "fit_score": concept.fit_score,
                "domain_tags": concept.domain_tags,
                "risks": concept.risks,
                "created_by": str(concept.created_by),
                "created_at": concept.created_at.isoformat(),
            }
        except ConceptCandidateModel.DoesNotExist:
            return None
