"""
Abstraction rule generation API.
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.errors import settings_required_response, validation_error_response
from app.application.use_cases.abstraction.generate_abstraction import (
    generate_abstraction,
    generate_abstractions_for_session,
)
from app.core.database import get_db
from app.infrastructure.ai_clients.factory import SettingsRequiredError
from app.models.abstraction import AbstractionRule

router = APIRouter(tags=["abstraction"])


class AbstractionRequest(BaseModel):
    source_type: str  # reference | sketch | concept
    source_id: uuid.UUID | None = None


class AbstractionRuleResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID | None
    form: str | None
    structure: str | None
    surface: str | None
    color_material: str | None
    meaning: str | None
    usability: str | None
    axes_count: int
    sketch_prompt: str | None
    risk_notes: str | None

    class Config:
        from_attributes = True


@router.post("/sessions/{session_id}/abstractions", response_model=list[AbstractionRuleResponse])
async def api_generate_abstraction(
    session_id: uuid.UUID,
    body: AbstractionRequest,
    db: Session = Depends(get_db),
):
    try:
        if body.source_id is None:
            rules = await generate_abstractions_for_session(db, session_id, body.source_type)
            return rules
        rule = await generate_abstraction(db, session_id, body.source_type, body.source_id)
        return [rule]
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except ValueError as exc:
        return validation_error_response(str(exc))


@router.get("/sessions/{session_id}/abstractions", response_model=list[AbstractionRuleResponse])
def api_list_abstractions(session_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(AbstractionRule)
        .filter_by(session_id=session_id)
        .order_by(AbstractionRule.created_at.desc())
        .all()
    )
