"""
Ideas API endpoints for Fashion AI Generation System
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.sessions import get_sessions_snapshot

router = APIRouter()


class IdeaResponse(BaseModel):
    id: Optional[str]
    session_id: int
    title: Optional[str]
    summary: Optional[str]
    status: Optional[str]
    created_at: Optional[str]


def _collect_ideas(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ideas: List[Dict[str, Any]] = []
    for session in sessions:
        results = session.get("pipeline_results") or {}
        design_ideas = results.get("design_ideas") or []
        for index, idea in enumerate(design_ideas):
            ideas.append({
                "id": f"{session.get('id')}-{index + 1}",
                "session_id": session.get("id"),
                "title": idea.get("concept_name") or idea.get("title") or idea.get("concept"),
                "summary": idea.get("summary") or idea.get("description") or idea.get("rationale"),
                "status": idea.get("status"),
                "created_at": session.get("completed_at") or session.get("created_at")
            })
    return ideas


@router.get("/", response_model=List[IdeaResponse])
async def list_ideas(
    session_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    sessions = get_sessions_snapshot()
    if session_id:
        sessions = [s for s in sessions if s.get("id") == session_id]

    ideas = _collect_ideas(sessions)
    if status:
        ideas = [idea for idea in ideas if idea.get("status") == status]
    return ideas
