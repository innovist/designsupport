"""
Reference asset search and analysis API.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.errors import (
    copyright_blocked_response,
    not_found_response,
    settings_required_response,
    validation_error_response,
)
from app.application.dtos.reference_dtos import (
    ReferenceAnalysisResponse,
    ReferenceAssetResponse,
    ReferenceRiskUpdate,
)
from app.application.use_cases.references.search_references import (
    analyze_reference,
    search_references,
    update_reference_risk,
)
from app.core.database import get_db
from app.infrastructure.ai_clients.factory import SettingsRequiredError
from app.models.references import ReferenceAsset

router = APIRouter(tags=["references"])


class ReferenceSearchRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    use_sketch_context: bool = False  # True: augment query with sketch analysis


@router.post("/sessions/{session_id}/references/search", response_model=list[ReferenceAssetResponse])
async def api_search_references(
    session_id: uuid.UUID,
    body: ReferenceSearchRequest,
    db: Session = Depends(get_db),
):
    query = body.query
    if body.use_sketch_context:
        query = _augment_query_with_sketch(db, session_id, query)
    try:
        return await search_references(db, session_id, query)
    except ValueError as exc:
        return validation_error_response(str(exc))


def _augment_query_with_sketch(db, session_id: uuid.UUID, base_query: str) -> str:
    """
    스케치 분석 결과의 form/structure 키워드를 검색어에 추가한다.
    분석 데이터가 없으면 원본 쿼리를 그대로 반환한다.
    """
    from app.models.assets import SketchAnalysis, UserSketchAsset
    sketch = (
        db.query(UserSketchAsset)
        .filter_by(session_id=session_id)
        .order_by(UserSketchAsset.created_at.desc())
        .first()
    )
    if not sketch:
        return base_query
    analysis = db.query(SketchAnalysis).filter_by(sketch_id=sketch.id).first()
    if not analysis:
        return base_query
    extras = []
    if analysis.form_elements:
        elements = analysis.form_elements
        if isinstance(elements, list):
            extras.extend(elements[:2])
    if analysis.intent and len(analysis.intent) < 80:
        extras.append(analysis.intent)
    if extras:
        return f"{base_query} {' '.join(extras)}"
    return base_query


@router.get("/sessions/{session_id}/references", response_model=list[ReferenceAssetResponse])
def api_list_references(session_id: uuid.UUID, db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    return (
        db.query(ReferenceAsset)
        .options(joinedload(ReferenceAsset.analysis))
        .filter_by(session_id=session_id)
        .order_by(ReferenceAsset.collected_at.desc())
        .all()
    )


@router.post("/references/{reference_id}/analyze", response_model=ReferenceAnalysisResponse)
async def api_analyze_reference(reference_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return await analyze_reference(db, reference_id)
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except PermissionError:
        return copyright_blocked_response(str(reference_id))
    except ValueError as exc:
        return not_found_response(str(exc))


@router.patch("/references/{reference_id}/risk", response_model=ReferenceAssetResponse)
def api_update_reference_risk(
    reference_id: uuid.UUID, body: ReferenceRiskUpdate, db: Session = Depends(get_db)
):
    try:
        return update_reference_risk(db, reference_id, body.copyright_risk, body.license_type)
    except ValueError as exc:
        return not_found_response(str(exc))
