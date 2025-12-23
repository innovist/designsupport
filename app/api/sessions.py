from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project, Session as ProjectSession
from app.api.session_schemas import SessionCreate, SessionUpdate, SessionResponse
from app.api import session_store
from app.api.session_store import get_session_record, serialize_session, update_metadata, start_pipeline

router = APIRouter()


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    project_id: Optional[int] = None,
    limit: int = 50,
    status: Optional[str] = None,
    sort: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    query = db.query(ProjectSession)
    if project_id:
        query = query.filter(ProjectSession.project_id == project_id)

    sessions = query.all()
    sessions = [session_store.sync_session_state(db, session) for session in sessions]
    serialized = [serialize_session(session) for session in sessions]
    if status:
        serialized = [s for s in serialized if s.get("status") == status]

    reverse = True if sort in (None, "created_at_desc") else False
    serialized.sort(key=lambda x: x.get("created_at", ""), reverse=reverse)
    return serialized[:limit]


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    if not db.query(Project.id).filter(Project.id == session_data.project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")

    metadata = {
        "user_keywords": session_data.user_keywords or [],
        "filters": session_data.filters or {},
        "input_text": session_data.input_text,
        "input_urls": session_data.input_urls or [],
        "input_files": [],
        "crawler_config": session_data.crawler_config.model_dump() if session_data.crawler_config else {},
        "auto_start": session_data.auto_start,
        "generate_images": session_data.generate_images,
        "generate_blueprints": session_data.generate_blueprints,
        "blueprint_size_system": session_data.blueprint_size_system,
        "blueprint_size": session_data.blueprint_size,
        "status": "created",
        "progress_percent": 0.0,
        "current_step": None,
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "logs": [],
        "pipeline_results": None
    }

    session = ProjectSession(
        project_id=session_data.project_id,
        name=session_data.session_title,
        description=session_data.description,
        metadata_json=metadata
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    if session_data.auto_start:
        await start_pipeline(session.id)

    return serialize_session(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = get_session_record(db, session_id)
    session = session_store.sync_session_state(db, session)
    return serialize_session(session)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_update: SessionUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    session = get_session_record(db, session_id)
    update_data = session_update.model_dump(exclude_unset=True)
    if "session_title" in update_data:
        session.name = update_data["session_title"]
    if "description" in update_data:
        session.description = update_data["description"]
    if "status" in update_data:
        update_metadata(session, {"status": update_data["status"]})
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return serialize_session(session)


@router.delete("/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    session = get_session_record(db, session_id)
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}


@router.get("/{session_id}/status")
async def get_session_status(session_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = get_session_record(db, session_id)
    session = session_store.sync_session_state(db, session)
    data = serialize_session(session)
    return {
        "session_id": session_id,
        "status": data.get("status", "created"),
        "progress_percent": data.get("progress_percent", 0.0),
        "current_step": data.get("current_step"),
        "error_message": data.get("error_message"),
        "started_at": data.get("started_at"),
        "completed_at": data.get("completed_at")
    }


@router.get("/{session_id}/logs")
async def get_session_logs(session_id: int, limit: int = 100, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = get_session_record(db, session_id)
    session = session_store.sync_session_state(db, session)
    logs = serialize_session(session).get("logs", [])
    return {
        "session_id": session_id,
        "logs": logs[-limit:],
        "total_count": len(logs)
    }


@router.post("/{session_id}/run-analysis")
async def run_analysis(session_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = get_session_record(db, session_id)
    session = session_store.sync_session_state(db, session)
    status = serialize_session(session).get("status")
    if status in ["running", "analyzing"]:
        return {"message": "Session already running", "status": status}
    await start_pipeline(session_id)
    return {"message": "Pipeline started", "session_id": session_id}


@router.get("/{session_id}/results")
async def get_session_results(session_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    session = get_session_record(db, session_id)
    session = session_store.sync_session_state(db, session)
    data = serialize_session(session)
    results = data.get("pipeline_results")
    status = data.get("status", "created")
    if status != "completed" or not results:
        return {
            "session_id": session_id,
            "status": status,
            "progress_percent": data.get("progress_percent", 0.0),
            "message": "Session not completed yet"
        }
    return {
        "session_id": session_id,
        "status": status,
        "summary": results.get("summary"),
        "trends": results.get("trends", []),
        "design_ideas": results.get("design_ideas", []),
        "generated_images": results.get("generated_images", []),
        "blueprints": results.get("blueprints", []),
        "completed_at": data.get("completed_at")
    }


@router.post("/{session_id}/upload-files")
async def upload_session_files(
    session_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    session = get_session_record(db, session_id)
    upload_dir = Path("uploads") / f"session_{session_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    for file in files:
        file_path = upload_dir / file.filename
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
        file_info = {
            "filename": file.filename,
            "path": str(file_path),
            "content_type": file.content_type,
            "size": len(content)
        }
        saved_files.append(file_info)

    metadata = serialize_session(session)
    input_files = list(metadata.get("input_files", []))
    input_files.extend(saved_files)
    update_metadata(session, {"input_files": input_files})
    session.updated_at = datetime.utcnow()
    db.commit()

    if metadata.get("auto_start") and metadata.get("status") == "created":
        await start_pipeline(session_id)

    return {"message": "Files uploaded", "files": saved_files}


def get_sessions_snapshot() -> List[Dict[str, Any]]:
    return session_store.get_sessions_snapshot()
