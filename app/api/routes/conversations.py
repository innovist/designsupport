"""
Chat conversation API.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errors import not_found_response, settings_required_response, validation_error_response
from app.application.dtos.session_dtos import MessageCreate, MessageResponse
from app.application.use_cases.conversations.send_message import get_messages, send_message
from app.core.database import get_db
from app.infrastructure.ai_clients.factory import SettingsRequiredError

router = APIRouter(tags=["conversations"])


@router.post("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def api_send_message(
    session_id: uuid.UUID, body: MessageCreate, db: Session = Depends(get_db)
):
    try:
        user_msg, assistant_msg = await send_message(db, session_id, body.content)
        return [user_msg, assistant_msg]
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except ValueError as exc:
        return not_found_response(str(exc))


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
def api_get_messages(session_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return get_messages(db, session_id)
    except ValueError as exc:
        return not_found_response(str(exc))
