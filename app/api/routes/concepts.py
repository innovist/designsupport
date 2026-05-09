"""
Concept generation and decision API.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errors import settings_required_response, validation_error_response
from app.application.dtos.concept_dtos import (
    ConceptCandidateResponse,
    ConceptDecisionCreate,
    ConceptDecisionResponse,
)
from app.application.use_cases.concepts.generate_concepts import (
    generate_concepts,
    record_concept_decision,
)
from app.core.database import get_db
from app.infrastructure.ai_clients.factory import SettingsRequiredError
from app.models.concepts import ConceptCandidate

router = APIRouter(tags=["concepts"])


@router.post("/sessions/{session_id}/concepts", response_model=list[ConceptCandidateResponse])
async def api_generate_concepts(session_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return await generate_concepts(db, session_id)
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except ValueError as exc:
        return validation_error_response(str(exc))


@router.get("/sessions/{session_id}/concepts", response_model=list[ConceptCandidateResponse])
def api_list_concepts(session_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(ConceptCandidate)
        .filter_by(session_id=session_id)
        .order_by(ConceptCandidate.score.desc())
        .all()
    )


@router.post("/concepts/{concept_id}/decisions", response_model=ConceptDecisionResponse)
def api_record_decision(
    concept_id: uuid.UUID, body: ConceptDecisionCreate, db: Session = Depends(get_db)
):
    try:
        return record_concept_decision(db, concept_id, body.decision, body.reason)
    except ValueError as exc:
        return validation_error_response(str(exc))
