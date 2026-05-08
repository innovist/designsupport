"""GetSessionDetail use case (read-only, not audited).

Returns session + brief + decisions.
"""
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from apps.design_sessions.application.ports import (
    BriefRepositoryPort,
    DecisionLogRepositoryPort,
    SessionRepositoryPort,
)
from apps.design_sessions.domain.entities import DecisionLog, DesignBrief, DesignSession
from shared.domain.exceptions import NotFoundError


@dataclass
class SessionDetail:
    """Composite view of a session with its brief and recent decisions."""

    session: DesignSession
    brief: Optional[DesignBrief]
    decisions: List[DecisionLog]


class GetSessionDetailUseCase:
    """Fetch session detail — read-only, not audited per spec."""

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        brief_repository: BriefRepositoryPort,
        decision_repository: DecisionLogRepositoryPort,
    ) -> None:
        self._session_repo = session_repository
        self._brief_repo = brief_repository
        self._decision_repo = decision_repository

    async def execute(self, session_id: UUID) -> SessionDetail:
        """Fetch session with brief and decisions.

        Args:
            session_id: Session UUID

        Returns:
            SessionDetail composite object

        Raises:
            NotFoundError: If session not found
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(entity_type="DesignSession", identifier=str(session_id))

        brief = await self._brief_repo.get_by_session(session_id)
        decisions = await self._decision_repo.list_by_session(session_id)

        return SessionDetail(session=session, brief=brief, decisions=decisions)
