"""Django ORM adapter for DesignSession port.

Implements SessionPort from design_sessions module.
"""
from uuid import UUID
from typing import Optional

from apps.specs.application.ports import SessionPort


class DjangoORMSessionAdapter(SessionPort):
    """Django ORM adapter for accessing design sessions."""

    async def get_session(self, session_id: UUID) -> Optional[dict]:
        """Get session data.

        Args:
            session_id: Session UUID

        Returns:
            Session data including brief, domain, user info
        """
        from apps.design_sessions.infrastructure.orm.models import DesignSession

        try:
            session = await DesignSession.objects.aget(id=str(session_id))
            return {
                "id": str(session.id),
                "project_id": str(session.project_id),
                "mode": session.mode,
                "status": session.status,
                "current_step": session.current_step,
                "version": session.version,
                "decision_required": session.decision_required,
                "started_by": str(session.started_by),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            }
        except DesignSession.DoesNotExist:
            return None

    async def session_exists(self, session_id: UUID) -> bool:
        """Check if session exists.

        Args:
            session_id: Session UUID

        Returns:
            True if exists, False otherwise
        """
        from apps.design_sessions.infrastructure.orm.models import DesignSession

        return await DesignSession.objects.filter(id=str(session_id)).aexists()

    async def get_session_brief(self, session_id: UUID) -> Optional[dict]:
        """Get brief data for a session.

        Args:
            session_id: Session UUID

        Returns:
            Brief data dictionary
        """
        from apps.design_sessions.infrastructure.orm.models import DesignBrief

        try:
            brief = await DesignBrief.objects.aget(session_id=str(session_id))
            return {
                "purpose": brief.purpose,
                "audience": brief.audience,
                "usage_context": brief.usage_context,
                "constraints": brief.constraints,
                "result_form": brief.result_form,
                "clarifying_questions": brief.clarifying_questions,
                "score": brief.score,
            }
        except DesignBrief.DoesNotExist:
            return {}

    async def get_session_domain(self, session_id: UUID) -> Optional[str]:
        """Get domain for a session.

        Args:
            session_id: Session UUID

        Returns:
            Domain identifier if found, None otherwise
        """
        from apps.design_sessions.infrastructure.orm.models import DesignSession
        from apps.design_projects.infrastructure.orm.models import DesignProject

        try:
            session = await DesignSession.objects.aget(id=str(session_id))
            project = await DesignProject.objects.aget(id=str(session.project_id))
            return project.domain
        except (DesignSession.DoesNotExist, DesignProject.DoesNotExist):
            return None
