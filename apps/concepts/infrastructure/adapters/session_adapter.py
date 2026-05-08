"""Adapter for design_sessions module port.

Implements SessionPort from concepts.application.ports.
"""
from typing import Optional
from uuid import UUID

from apps.concepts.application.ports import SessionPort
from shared.domain.exceptions import NotFoundError


class DesignSessionAdapter(SessionPort):
    """Adapter for accessing design sessions.

    This adapter connects to the design_sessions module to retrieve
    session brief data for concept scoring.
    """

    async def get_session_brief(self, session_id: UUID) -> Optional[dict]:
        """Get brief data for a session.

        Args:
            session_id: Session UUID

        Returns:
            Dict with brief data including keywords, tone, target_audience
            or None if session not found
        """
        try:
            # Import here to avoid circular dependencies
            from apps.design_sessions.application.use_cases.get_session_brief import GetSessionBriefUseCase
            from apps.design_sessions.infrastructure.repositories.session_repository import DjangoSessionRepository

            use_case = GetSessionBriefUseCase(DjangoSessionRepository())
            result = await use_case.execute(session_id)

            if result.is_failure:
                return None

            brief = result.value
            return {
                "keywords": brief.get("keywords", []),
                "tone": brief.get("tone"),
                "target_audience": brief.get("target_audience"),
                "project_name": brief.get("project_name"),
            }

        except ImportError:
            # design_sessions module not available
            return None
        except Exception:
            # Session not found or other error
            return None

    async def session_exists(self, session_id: UUID) -> bool:
        """Check if a session exists.

        Args:
            session_id: Session UUID

        Returns:
            True if session exists, False otherwise
        """
        brief = await self.get_session_brief(session_id)
        return brief is not None
