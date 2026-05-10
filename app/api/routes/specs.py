"""
Spec document generation and versioning API.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errors import not_found_response, validation_error_response
from app.application.dtos.generation_dtos import SpecDocumentResponse, SpecGenerationRequest
from app.application.use_cases.specs.generate_spec import generate_spec, version_spec
from app.core.database import get_db
from app.models.specs import SpecDocument

router = APIRouter(tags=["specs"])


@router.post("/sessions/{session_id}/specs", response_model=SpecDocumentResponse, status_code=201)
def api_generate_spec(
    session_id: uuid.UUID,
    request: SpecGenerationRequest | None = None,
    db: Session = Depends(get_db),
):
    try:
        selected_design_id = request.selected_design_id if request else None
        return generate_spec(db, session_id, selected_design_id)
    except ValueError as exc:
        return validation_error_response(str(exc))


@router.get("/sessions/{session_id}/specs", response_model=list[SpecDocumentResponse])
def api_list_specs(session_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(SpecDocument)
        .filter_by(session_id=session_id)
        .order_by(SpecDocument.version.desc())
        .all()
    )


@router.get("/specs/{spec_id}", response_model=SpecDocumentResponse)
def api_get_spec(spec_id: uuid.UUID, db: Session = Depends(get_db)):
    spec = db.get(SpecDocument, spec_id)
    if not spec:
        return not_found_response(f"SpecDocument {spec_id} not found")
    return spec


@router.post("/specs/{spec_id}/version", response_model=SpecDocumentResponse, status_code=201)
def api_version_spec(spec_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return version_spec(db, spec_id)
    except ValueError as exc:
        return validation_error_response(str(exc))
