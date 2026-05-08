"""Conversation domain entities.

Chat-based collaboration entities.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional


class MessageRole:
    """Chat message role value object."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Conversation:
    """Conversation aggregate root.

    Container for chat messages within a session.
    """

    id: UUID
    session_id: UUID
    created_at: datetime

    def __init__(
        self,
        session_id: UUID,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize a new conversation.

        Args:
            session_id: Parent design session UUID
            id: Conversation UUID
            created_at: Creation timestamp
        """
        self.id = id or uuid4()
        self.session_id = session_id
        self.created_at = created_at or _utcnow()


@dataclass
class ChatMessage:
    """Chat message entity.

    Individual message within a conversation.
    """

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    evidence_refs: List[Dict[str, Any]]
    is_hypothesis: bool
    created_at: datetime

    def __init__(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        is_hypothesis: bool = False,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize a new chat message.

        Args:
            conversation_id: Parent conversation UUID
            role: Message role (user/assistant/system)
            content: Message content
            evidence_refs: Supporting evidence references
            is_hypothesis: Whether AI message is hypothetical
            id: Message UUID
            created_at: Timestamp
        """
        self.id = id or uuid4()
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.evidence_refs = evidence_refs or []
        self.is_hypothesis = is_hypothesis
        self.created_at = created_at or _utcnow()
        self._validate_invariant()

    def _validate_invariant(self) -> None:
        """Enforce INV-01-03: AI messages must have evidence_refs or is_hypothesis.

        Raises:
            InvariantViolationError: If invariant is broken
        """
        if self.is_ai_message() and not self.evidence_refs and not self.is_hypothesis:
            from shared.domain.exceptions import InvariantViolationError
            raise InvariantViolationError(
                invariant="INV-01-03",
                details={
                    "role": self.role,
                    "evidence_refs": self.evidence_refs,
                    "is_hypothesis": self.is_hypothesis,
                    "message": "AI messages must include evidence_refs or be marked is_hypothesis=True",
                },
            )

    def is_ai_message(self) -> bool:
        """Check if this is an AI message."""
        return self.role in {MessageRole.ASSISTANT, MessageRole.SYSTEM}

    def requires_evidence(self) -> bool:
        """Check if AI message requires evidence.

        Returns:
            True if AI message without evidence or hypothesis flag
        """
        if not self.is_ai_message():
            return False
        return not self.evidence_refs and not self.is_hypothesis
