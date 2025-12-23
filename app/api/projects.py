"""
Project CRUD API for Fashion AI Generation System
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project, ProjectStatus
from app.api.project_schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.api import project_store
from app.api.project_store import project_to_dict, get_session_counts, apply_project_update, build_project_model

router = APIRouter()


def _status_value(project: Project) -> str:
    return project.status.value if isinstance(project.status, ProjectStatus) else str(project.status)


def get_projects_snapshot() -> List[Dict[str, Any]]:
    return project_store.get_projects_snapshot()


def project_exists(project_id: int) -> bool:
    return project_store.project_exists(project_id)


def get_project_snapshot(project_id: int) -> Optional[Dict[str, Any]]:
    return project_store.get_project_snapshot(project_id)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List projects"""
    query = db.query(Project)
    if status:
        try:
            status_enum = ProjectStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}") from exc
        query = query.filter(Project.status == status_enum)

    projects = (
        query.order_by(Project.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    session_counts = get_session_counts(db, [p.id for p in projects])
    return [project_to_dict(p, session_counts.get(p.id, 0)) for p in projects]


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create project"""
    project = build_project_model(project_data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_to_dict(project, session_count=0)


@router.get("/stats")
async def get_project_stats() -> Dict[str, Any]:
    """Dashboard stats"""
    from app.api.sessions import get_sessions_snapshot
    from app.services.chat_store import get_chat_session_count

    sessions = get_sessions_snapshot()
    total_sessions = len(sessions)
    total_ideas = sum(s.get("ideas_count", 0) for s in sessions)
    total_crawled = sum(s.get("crawled_count", 0) for s in sessions)
    total_chats = get_chat_session_count()

    return {
        "total_sessions": total_sessions,
        "total_ideas": total_ideas,
        "total_crawled": total_crawled,
        "total_chats": total_chats
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    counts = get_session_counts(db, [project_id])
    return project_to_dict(project, counts.get(project_id, 0))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.model_dump(exclude_unset=True)
    apply_project_update(project, update_data)
    db.commit()
    db.refresh(project)
    counts = get_session_counts(db, [project_id])
    return project_to_dict(project, counts.get(project_id, 0))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def patch_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Patch project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.model_dump(exclude_unset=True)
    apply_project_update(project, update_data)
    db.commit()
    db.refresh(project)
    counts = get_session_counts(db, [project_id])
    return project_to_dict(project, counts.get(project_id, 0))


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Delete project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/start")
async def start_project(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Start project (auto pipeline)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if _status_value(project) not in ["draft", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start project in {_status_value(project)} status"
        )

    project.start()
    project.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Project started",
        "project_id": project_id,
        "status": _status_value(project)
    }


@router.post("/{project_id}/cancel")
async def cancel_project(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Cancel project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.cancel()
    project.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Project cancelled",
        "project_id": project_id,
        "status": _status_value(project)
    }


@router.get("/{project_id}/status")
async def get_project_status(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get project status"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project_id,
        "status": _status_value(project),
        "progress_percent": project.progress_percent,
        "started_at": project.started_at.isoformat() if project.started_at else None,
        "completed_at": project.completed_at.isoformat() if project.completed_at else None
    }
