"""
Use-case: append a user message, call the AI, store the response.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage as PortAIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.infrastructure.repositories.session_repository import SessionRepository
from app.models.session import ChatMessage

logger = get_logger(__name__)


async def send_message(
    db: Session, session_id: uuid.UUID, content: str
) -> tuple[ChatMessage, ChatMessage]:
    """
    Save user message, call AI, save assistant reply.
    Returns (user_msg, assistant_msg).
    """
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=content,
        stage=session.pipeline_stage,
    )
    db.add(user_msg)
    db.flush()

    history = [
        PortAIMessage(role=m.role, content=m.content)
        for m in session.messages
        if not m.id == user_msg.id
    ]
    history.append(PortAIMessage(role="user", content=content))

    logger.info("[CHAT] session=%s calling AI feature=chat history_len=%d", session_id, len(history))
    client = await get_ai_client(db, "chat")
    response = await client.complete(history, temperature=0.7, max_tokens=2000)
    logger.info("[CHAT] session=%s AI replied len=%d", session_id, len(response.content))

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response.content,
        stage=session.pipeline_stage,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)
    return user_msg, assistant_msg


def get_messages(db: Session, session_id: uuid.UUID) -> list[ChatMessage]:
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    return session.messages
