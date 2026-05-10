"""
Use-case: extract and structure a DesignBrief from the session's conversation history.

If any mandatory field is missing the AI is asked to generate a clarifying question
which is stored as an assistant ChatMessage.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.infrastructure.repositories.session_repository import SessionRepository
from app.models.session import DesignBrief, ChatMessage
from app.utils.json_parse import parse_json_object

logger = get_logger(__name__)

_MANDATORY_FIELDS = ("purpose", "domain", "target_user", "result_form")

_STRUCTURE_PROMPT = """
You are a design brief analyst. Given the conversation below, extract the following fields:
- purpose: What the designer wants to create (required)
- domain: Design domain (industrial / product_service / visual / advertising / general) (required)
- target_user: Who will use the product (required)
- context: Situation or environment of use (optional)
- constraints: Budget, material, or technical limits (optional)
- use_case: Specific usage scenario (optional)
- result_form: Expected output type e.g. "product sketch", "brand guideline" (required)

Return ONLY a JSON object with these keys. Missing optional fields should be null.
If you cannot determine a required field, set it to null.

Conversation:
{conversation}
"""

_CLARIFY_PROMPT = """
The user's design brief is incomplete. Missing required fields: {missing}.
Generate ONE focused question to gather the missing information.
Keep the question friendly and brief. Return only the question text.
"""


async def structure_brief(db: Session, session_id: uuid.UUID) -> DesignBrief:
    """
    Parse conversation history and upsert DesignBrief.
    Returns the Brief object (is_complete indicates whether all fields are present).
    """
    session_repo = SessionRepository(db)
    session = session_repo.get_by_id(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    messages = session.messages
    if not messages:
        raise ValueError("Session has no messages to structure a brief from")

    logger.info("[BRIEF] structuring session=%s message_count=%d", session_id, len(messages))

    conversation_text = "\n".join(
        f"{m.role.upper()}: {m.content}" for m in messages
    )

    client = await get_ai_client(db, "brief_structuring")
    prompt = _STRUCTURE_PROMPT.format(conversation=conversation_text)

    response = await client.complete(
        [AIMessage(role="user", content=prompt)],
        temperature=0.3,
        max_tokens=1000,
    )

    try:
        extracted = parse_json_object(response.content)
    except Exception:
        logger.warning("Failed to parse brief JSON from AI response: %s", response.content[:200])
        extracted = {}

    missing = [f for f in _MANDATORY_FIELDS if not extracted.get(f)]

    if missing:
        clarify_prompt = _CLARIFY_PROMPT.format(missing=", ".join(missing))
        clarify_response = await client.complete(
            [AIMessage(role="user", content=clarify_prompt)],
            temperature=0.5,
            max_tokens=200,
        )
        question_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=clarify_response.content.strip(),
            stage="brief_input",
        )
        db.add(question_msg)
        db.flush()

    brief = session_repo.upsert_brief(
        session_id=session_id,
        fields={**extracted, "is_complete": len(missing) == 0},
    )
    db.commit()
    db.refresh(brief)
    logger.info("[BRIEF] structured session=%s is_complete=%s missing=%s",
                session_id, len(missing) == 0, missing or None)
    return brief
