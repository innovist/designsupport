"""
Projects and sessions API.
"""

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import not_found_response, validation_error_response
from app.application.dtos.session_dtos import (
    BriefResponse,
    BriefUpdate,
    ProjectCreate,
    ProjectResponse,
    SessionCreate,
    SessionResponse,
    SessionStageUpdate,
)
from app.application.use_cases.sessions.create_session import create_project, create_session
from app.application.use_cases.sessions.get_session_detail import get_session_detail
from app.application.use_cases.sessions.rerun_step import rerun_step
from app.application.use_cases.sessions.structure_brief import structure_brief
from app.core.database import get_db
from app.core.logging import get_logger, log_pipeline_stage
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.infrastructure.repositories.workspace_repository import WorkspaceRepository

router = APIRouter(tags=["sessions"])
logger = get_logger(__name__)


# --- Projects ---

@router.post("/projects", response_model=ProjectResponse, status_code=201)
def api_create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    return create_project(db, data)


@router.get("/projects", response_model=list[ProjectResponse])
def api_list_projects(db: Session = Depends(get_db)):
    workspace = WorkspaceRepository(db).ensure_default_workspace()
    return ProjectRepository(db).list_all(workspace.id)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def api_get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get_by_id(project_id)
    if not project:
        return not_found_response(f"Project {project_id} not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def api_update_project(
    project_id: uuid.UUID,
    body: dict[str, Any],
    db: Session = Depends(get_db),
):
    project = ProjectRepository(db).get_by_id(project_id)
    if not project:
        return not_found_response(f"Project {project_id} not found")
    for field in ("name", "domain", "purpose", "status"):
        if field in body:
            setattr(project, field, body[field])
    db.commit()
    db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
def api_delete_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    project = ProjectRepository(db).get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    db.delete(project)
    db.commit()
    return None


# --- Sessions ---

@router.post("/sessions", response_model=SessionResponse, status_code=201)
def api_create_session(data: SessionCreate, db: Session = Depends(get_db)):
    try:
        return create_session(db, data)
    except Exception as exc:
        return validation_error_response(str(exc))


@router.get("/sessions", response_model=list[SessionResponse])
def api_list_sessions(
    project_id: uuid.UUID | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    from app.models.session import DesignSession
    from app.infrastructure.repositories.session_repository import SessionRepository

    if project_id:
        return SessionRepository(db).list_for_project(project_id)[:limit]
    return (
        db.query(DesignSession)
        .order_by(DesignSession.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def api_get_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        session = get_session_detail(db, session_id)
        return session
    except ValueError as exc:
        return not_found_response(str(exc))


@router.delete("/sessions/{session_id}", status_code=204)
def api_delete_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    from app.models.session import DesignSession

    session = db.get(DesignSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    db.delete(session)
    db.commit()
    return None


@router.patch("/sessions/{session_id}/stage", response_model=SessionResponse)
def api_update_stage(
    session_id: uuid.UUID, body: SessionStageUpdate, db: Session = Depends(get_db)
):
    from app.infrastructure.repositories.session_repository import SessionRepository
    try:
        log_pipeline_stage(str(session_id), body.pipeline_stage)
        return SessionRepository(db).update_stage(session_id, body.pipeline_stage)
    except ValueError as exc:
        return not_found_response(str(exc))


@router.post("/sessions/{session_id}/brief", response_model=BriefResponse)
async def api_structure_brief(
    session_id: uuid.UUID,
    body: BriefUpdate | None = None,
    db: Session = Depends(get_db),
):
    from app.infrastructure.ai_clients.factory import SettingsRequiredError
    from app.api.errors import settings_required_response

    try:
        if body and any(value is not None for value in body.model_dump().values()):
            from app.infrastructure.repositories.session_repository import SessionRepository
            fields = body.model_dump()
            mandatory = ("purpose",)
            fields["is_complete"] = all(fields.get(key) for key in mandatory)
            return SessionRepository(db).upsert_brief(session_id, fields)
        brief = await structure_brief(db, session_id)
        return brief
    except SettingsRequiredError as exc:
        return settings_required_response(exc)
    except ValueError as exc:
        return validation_error_response(str(exc))


@router.post("/sessions/{session_id}/rerun", response_model=SessionResponse)
def api_rerun_step(session_id: uuid.UUID, body: SessionStageUpdate, db: Session = Depends(get_db)):
    try:
        return rerun_step(db, session_id, body.pipeline_stage)
    except ValueError as exc:
        return validation_error_response(str(exc))


# ─── Auto pipeline ────────────────────────────────────────────────────────────

# @MX:WARN: [AUTO] Background task with isolated DB session lifecycle
# @MX:REASON: Async context manager + task scheduling - risk of session leaks if exceptions occur

async def _run_pipeline_background(session_id: uuid.UUID, options: dict | None = None) -> None:
    """BackgroundTask: runs in a new DB session to avoid request-session conflicts."""
    from app.core.database import SessionLocal
    from app.application.services.pipeline_orchestrator import DesignPipelineOrchestrator

    with SessionLocal() as db:
        orchestrator = DesignPipelineOrchestrator(session_id, db, options=options)
        await orchestrator.run()


@router.post("/sessions/{session_id}/auto", status_code=202)
async def api_start_auto_pipeline(
    session_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    body: dict[str, Any] | None = None,
    db: Session = Depends(get_db),
):
    """
    자동 파이프라인 시작.
    브리프가 완성되어 있어야 한다.
    202 Accepted를 반환하고 백그라운드에서 파이프라인을 실행한다.
    """
    from app.infrastructure.repositories.session_repository import SessionRepository
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        return not_found_response(f"Session {session_id} not found")

    brief = session.brief
    if not brief or not brief.is_complete:
        return validation_error_response(
            "브리프가 완성되지 않았습니다. 브리프를 먼저 완성해 주세요."
        )

    if session.pipeline_stage not in ("brief_input", "review_ready", "failed"):
        return validation_error_response(
            f"현재 단계({session.pipeline_stage})에서는 자동 모드를 시작할 수 없습니다."
        )

    repo.set_auto_mode(session_id)
    options = body if isinstance(body, dict) else {}
    background_tasks.add_task(_run_pipeline_background, session_id, options)
    logger.info("[SESSION] auto pipeline started session=%s", session_id)
    return {"status": "accepted", "session_id": str(session_id), "message": "자동 파이프라인이 시작되었습니다."}


@router.get("/sessions/{session_id}/progress")
def api_get_progress(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """자동 파이프라인 진행 상황 폴링 엔드포인트."""
    from app.infrastructure.repositories.session_repository import SessionRepository
    repo = SessionRepository(db)
    try:
        return repo.get_progress(session_id)
    except ValueError as exc:
        return not_found_response(str(exc))


# ─── Dashboard ────────────────────────────────────────────────────────────────

# @MX:WARN: [AUTO] Complex dashboard aggregation with 5+ table joins and nested queries
# @MX:REASON: High cyclomatic complexity (12+ branches) - N+1 query risk if sessions grow

@router.get("/dashboard")
def api_get_dashboard(db: Session = Depends(get_db)):
    """홈 대시보드용 요약 정보."""
    from app.models.session import DesignSession
    from app.models.generation import GeneratedDesign
    from app.infrastructure.repositories.project_repository import ProjectRepository
    from app.infrastructure.repositories.workspace_repository import WorkspaceRepository

    workspace = WorkspaceRepository(db).ensure_default_workspace()
    projects = ProjectRepository(db).list_all(workspace.id)
    project_ids = [p.id for p in projects]

    sessions = (
        db.query(DesignSession)
        .filter(DesignSession.project_id.in_(project_ids))
        .order_by(DesignSession.created_at.desc())
        .limit(20)
        .all()
    ) if project_ids else []

    project_map = {p.id: p.name for p in projects}
    active_stages = {"researching", "concepting", "referencing", "abstracting", "generating", "documenting"}

    completed_count = sum(1 for s in sessions if s.pipeline_stage == "review_ready")
    active_count = sum(1 for s in sessions if s.pipeline_stage in active_stages)

    design_count = (
        db.query(GeneratedDesign)
        .filter(GeneratedDesign.session_id.in_([s.id for s in sessions]))
        .count()
    ) if sessions else 0

    recent_sessions = [
        {
            "id": str(s.id),
            "title": (s.brief.purpose if s.brief else None) or "브리프 미입력",
            "pipeline_stage": s.pipeline_stage,
            "status": s.status,
            "mode": s.mode,
            "domain": s.brief.domain if s.brief else None,
            "project_id": str(s.project_id),
            "project_name": project_map.get(s.project_id, ""),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions[:10]
    ]

    return {
        "projects_count": len(projects),
        "active_sessions_count": active_count,
        "completed_sessions_count": completed_count,
        "generated_designs_count": design_count,
        "recent_sessions": recent_sessions,
    }
