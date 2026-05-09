"""
Sketch upload and analysis API.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.errors import not_found_response, settings_required_response, validation_error_response
from app.application.dtos.asset_dtos import (
    SketchAnalysisResponse,
    SketchAssetResponse,
    SketchConfirmRequest,
)
from app.application.use_cases.assets.analyze_sketch import (
    analyze_sketch,
    confirm_sketch_analysis,
)
from app.application.use_cases.assets.upload_sketch import upload_sketch
from app.core.database import get_db
from app.infrastructure.ai_clients.factory import SettingsRequiredError
from app.models.assets import SketchAnalysis, UserSketchAsset

router = APIRouter(tags=["assets"])


@router.post("/sessions/{session_id}/sketches", response_model=SketchAssetResponse, status_code=201)
async def api_upload_sketch(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    memo: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    try:
        return await upload_sketch(db, session_id, file, memo)
    except ValueError as exc:
        return validation_error_response(str(exc))


@router.get("/sessions/{session_id}/sketches", response_model=list[SketchAssetResponse])
def api_list_sketches(session_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(UserSketchAsset)
        .filter_by(session_id=session_id, is_deleted=False)
        .order_by(UserSketchAsset.created_at.desc())
        .all()
    )


@router.get("/sketches/{sketch_id}", response_model=SketchAssetResponse)
def api_get_sketch(sketch_id: uuid.UUID, db: Session = Depends(get_db)):
    sketch = db.get(UserSketchAsset, sketch_id)
    if not sketch or sketch.is_deleted:
        return not_found_response(f"Sketch {sketch_id} not found")
    return sketch


@router.get("/sketches/{sketch_id}/analysis", response_model=SketchAnalysisResponse)
def api_get_sketch_analysis(sketch_id: uuid.UUID, db: Session = Depends(get_db)):
    analysis = db.query(SketchAnalysis).filter_by(sketch_id=sketch_id).first()
    if not analysis:
        return not_found_response(f"No analysis for sketch {sketch_id}")
    return analysis


@router.post("/sketches/{sketch_id}/analyze", response_model=SketchAnalysisResponse)
async def api_analyze_sketch(sketch_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return await analyze_sketch(db, sketch_id)
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except ValueError as exc:
        return not_found_response(str(exc))


@router.post("/sketches/{sketch_id}/confirm-analysis", response_model=SketchAnalysisResponse)
def api_confirm_analysis(
    sketch_id: uuid.UUID, body: SketchConfirmRequest, db: Session = Depends(get_db)
):
    try:
        return confirm_sketch_analysis(db, sketch_id, body.confirmed, body.corrections)
    except ValueError as exc:
        return not_found_response(str(exc))
