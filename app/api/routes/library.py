"""Image library API — aggregates generated designs across all sessions/projects."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.generation import GeneratedDesign
from app.models.project import DesignProject
from app.models.session import DesignBrief, DesignSession

router = APIRouter(tags=["library"])


@router.get("/v1/library", include_in_schema=False)
@router.get("/library")
def api_list_library(
    project_id: Optional[uuid.UUID] = Query(None),
    session_id: Optional[uuid.UUID] = Query(None),
    image_type: Optional[str] = Query(None, include_in_schema=False),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort: str = Query("created_at_desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    base_filter = (
        GeneratedDesign.status == "completed",
        GeneratedDesign.image_path.isnot(None),
    )

    count_q = db.query(GeneratedDesign).filter(*base_filter)
    data_q = (
        db.query(
            GeneratedDesign,
            DesignSession.project_id.label("_project_id"),
            DesignProject.name.label("_project_name"),
            DesignBrief.purpose.label("_session_title"),
        )
        .join(DesignSession, DesignSession.id == GeneratedDesign.session_id)
        .join(DesignProject, DesignProject.id == DesignSession.project_id)
        .outerjoin(DesignBrief, DesignBrief.session_id == DesignSession.id)
        .filter(*base_filter)
    )

    if project_id:
        count_q = count_q.join(DesignSession, DesignSession.id == GeneratedDesign.session_id).filter(
            DesignSession.project_id == project_id
        )
        data_q = data_q.filter(DesignSession.project_id == project_id)
    if session_id:
        count_q = count_q.filter(GeneratedDesign.session_id == session_id)
        data_q = data_q.filter(GeneratedDesign.session_id == session_id)
    if date_from:
        count_q = count_q.filter(GeneratedDesign.created_at >= date_from)
        data_q = data_q.filter(GeneratedDesign.created_at >= date_from)
    if date_to:
        count_q = count_q.filter(GeneratedDesign.created_at <= date_to + "T23:59:59")
        data_q = data_q.filter(GeneratedDesign.created_at <= date_to + "T23:59:59")

    total = count_q.count()

    sort_col = _resolve_sort(sort)
    rows = data_q.order_by(sort_col).offset((page - 1) * limit).limit(limit).all()

    images = [_serialize(row) for row in rows]

    return {
        "images": images,
        "total": total,
        "stats": {
            "total": total,
            "design": total,
            "model": 0,
            "blueprint": 0,
        },
    }


def _resolve_sort(sort_key: str):
    mapping = {
        "created_at_desc": GeneratedDesign.created_at.desc(),
        "created_at_asc": GeneratedDesign.created_at.asc(),
        "name_asc": GeneratedDesign.prompt.asc(),
    }
    return mapping.get(sort_key, GeneratedDesign.created_at.desc())


def _serialize(row) -> dict:
    design = row[0]
    project_name = row._project_name or "-"
    session_title = row._session_title or "브리프 미입력"

    image_url = design.image_url

    return {
        "id": str(design.id),
        "type": "design",
        "title": session_title,
        "url": image_url,
        "path": image_url,
        "session_title": session_title,
        "project_name": project_name,
        "created_at": design.created_at.isoformat() if design.created_at else None,
        "prompt": design.prompt,
        "provider": design.provider,
        "model": design.model,
        "filename": _extract_filename(design.image_path),
    }


def _extract_filename(path: str | None) -> str:
    if not path:
        return "image.png"
    return path.rsplit("/", 1)[-1] if "/" in path else path
