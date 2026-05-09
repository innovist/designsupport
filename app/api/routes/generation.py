"""
Image generation API.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.errors import not_found_response, settings_required_response, validation_error_response
from app.application.dtos.generation_dtos import GeneratedDesignResponse, GenerationRequest
from app.application.use_cases.generation.create_generation_job import (
    create_generation_job,
    get_generation_result,
)
from app.core.database import get_db
from app.infrastructure.ai_clients.factory import SettingsRequiredError
from app.models.generation import GeneratedDesign

router = APIRouter(tags=["generation"])


@router.post("/sessions/{session_id}/generations", response_model=GeneratedDesignResponse, status_code=202)
def api_create_generation(
    session_id: uuid.UUID,
    body: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        return create_generation_job(db, session_id, body, background_tasks)
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except ValueError as exc:
        return validation_error_response(str(exc))


@router.get("/sessions/{session_id}/generations", response_model=list[GeneratedDesignResponse])
def api_list_generations(session_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(GeneratedDesign)
        .filter_by(session_id=session_id)
        .order_by(GeneratedDesign.created_at.desc())
        .all()
    )


@router.get("/generations/{generation_id}", response_model=GeneratedDesignResponse)
def api_get_generation(generation_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return get_generation_result(db, generation_id)
    except ValueError as exc:
        return not_found_response(str(exc))
