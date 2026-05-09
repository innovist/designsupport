"""
Trend search and source management API.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.errors import settings_required_response, validation_error_response
from app.application.use_cases.trends.search_trends import search_trends
from app.core.database import get_db
from app.infrastructure.ai_clients.factory import SettingsRequiredError
from app.infrastructure.repositories.trend_repository import TrendRepository
from app.models.trends import TrendInsight, TrendSource

router = APIRouter(tags=["trends"])


class TrendSearchRequest(BaseModel):
    query: str
    domain: Optional[str] = None


class TrendSourceCreate(BaseModel):
    name: str
    url: Optional[str] = None
    domain: Optional[str] = None


@router.post("/sessions/{session_id}/trends/search")
async def api_search_trends(
    session_id: uuid.UUID,
    body: TrendSearchRequest,
    db: Session = Depends(get_db),
):
    from app.models.session import DesignSession
    from fastapi.responses import JSONResponse
    if not db.get(DesignSession, session_id):
        return JSONResponse(status_code=404, content={"detail": "Session not found"})
    try:
        insights = await search_trends(db, session_id, body.query, body.domain)
        return {"count": len(insights), "insights": [_serialize_insight(i) for i in insights]}
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except Exception as exc:
        return validation_error_response(str(exc))


@router.get("/sessions/{session_id}/trends")
def api_list_session_trends(session_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.models.session import DesignSession
    from fastapi.responses import JSONResponse
    if not db.get(DesignSession, session_id):
        return JSONResponse(status_code=404, content={"detail": "Session not found"})
    insights = (
        db.query(TrendInsight)
        .join(TrendInsight.document)
        .filter(TrendInsight.session_id == session_id)
        .filter(TrendInsight.is_hypothesis == False)  # noqa: E712
        .all()
    )
    return {"count": len(insights), "insights": [_serialize_insight(i) for i in insights]}


@router.get("/trend-sources")
def api_list_trend_sources(db: Session = Depends(get_db)):
    sources = TrendRepository(db).list_all_sources()
    return [_serialize_source(s) for s in sources]


@router.post("/trend-sources", status_code=201)
def api_create_trend_source(body: TrendSourceCreate, db: Session = Depends(get_db)):
    source = TrendRepository(db).create_source(body.name, body.url, body.domain)
    return _serialize_source(source)


def _serialize_insight(i: TrendInsight) -> dict:
    return {
        "id": str(i.id),
        "summary": i.summary,
        "keywords": i.keywords,
        "evidence_quote": i.evidence_quote,
        "confidence_score": i.confidence_score,
        "is_hypothesis": i.is_hypothesis,
        "source_url": i.document.url if i.document else None,
    }


def _serialize_source(s: TrendSource) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "url": s.url,
        "domain": s.domain,
        "is_active": s.is_active,
    }
