"""
Project data helpers for API
"""

from datetime import datetime
import json
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.models.project import Project, ProjectStatus, Session as ProjectSession, Gender, Season


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _parse_enum(enum_cls: Any, value: Optional[str], field_name: str):
    if value is None:
        return None
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {value}") from exc


def project_to_dict(project: Project, session_count: int = 0) -> Dict[str, Any]:
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "prompt": project.prompt,
        "gender": _enum_value(project.gender),
        "age_group": project.age_group,
        "season": _enum_value(project.season),
        "region": project.region,
        "target_audience": project.target_audience,
        "language": project.language,
        "size_standard": project.size_standard,
        "crawl_sources": project.crawl_sources,
        "crawl_keywords": project.crawl_keywords,
        "max_crawl_pages": project.max_crawl_pages,
        "preferred_image_model": project.preferred_image_model,
        "status": _enum_value(project.status),
        "progress_percent": project.progress_percent,
        "session_count": session_count,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "started_at": project.started_at.isoformat() if project.started_at else None,
        "completed_at": project.completed_at.isoformat() if project.completed_at else None
    }


def get_session_counts(db: Session, project_ids: List[int]) -> Dict[int, int]:
    if not project_ids:
        return {}
    rows = (
        db.query(ProjectSession.project_id, func.count(ProjectSession.id))
        .filter(ProjectSession.project_id.in_(project_ids))
        .group_by(ProjectSession.project_id)
        .all()
    )
    return {project_id: count for project_id, count in rows}


def get_projects_snapshot() -> List[Dict[str, Any]]:
    with get_db_session() as db:
        projects = db.query(Project).all()
        counts = get_session_counts(db, [p.id for p in projects])
        return [project_to_dict(p, counts.get(p.id, 0)) for p in projects]


def project_exists(project_id: int) -> bool:
    with get_db_session() as db:
        return db.query(Project.id).filter(Project.id == project_id).first() is not None


def get_project_snapshot(project_id: int) -> Optional[Dict[str, Any]]:
    with get_db_session() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        counts = get_session_counts(db, [project.id])
        return project_to_dict(project, counts.get(project.id, 0))


def apply_project_update(project: Project, update_data: Dict[str, Any]) -> None:
    if "crawl_sources" in update_data and update_data["crawl_sources"] is not None:
        update_data["crawl_sources"] = json.dumps(update_data["crawl_sources"])
    if "crawl_keywords" in update_data and update_data["crawl_keywords"] is not None:
        update_data["crawl_keywords"] = json.dumps(update_data["crawl_keywords"])
    if "gender" in update_data:
        update_data["gender"] = _parse_enum(Gender, update_data.get("gender"), "gender")
    if "season" in update_data:
        update_data["season"] = _parse_enum(Season, update_data.get("season"), "season")

    for field, value in update_data.items():
        setattr(project, field, value)
    project.updated_at = datetime.utcnow()


def build_project_model(data: Any) -> Project:
    return Project(
        title=data.title,
        description=data.description,
        prompt=data.prompt,
        gender=_parse_enum(Gender, data.gender, "gender"),
        age_group=data.age_group,
        season=_parse_enum(Season, data.season, "season"),
        region=data.region,
        target_audience=data.target_audience,
        language=data.language,
        size_standard=data.size_standard,
        crawl_sources=json.dumps(data.crawl_sources or []),
        crawl_keywords=json.dumps(data.crawl_keywords or []),
        max_crawl_pages=data.max_crawl_pages,
        preferred_image_model=data.preferred_image_model,
        status=ProjectStatus.DRAFT,
        progress_percent=0
    )
