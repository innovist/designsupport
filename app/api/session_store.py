"""
Session data helpers for API
"""

from datetime import datetime
from typing import List, Dict, Any
import asyncio

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.logging import get_logger
from app.services.pipeline_orchestrator import FashionPipelineOrchestrator
from app.services.report_generation_service import ReportGenerationService
from app.models.project import Session as ProjectSession, Project

logger = get_logger(__name__)
_running_tasks: Dict[int, asyncio.Task] = {}


def _get_metadata(session: ProjectSession) -> Dict[str, Any]:
    return dict(session.metadata_json or {})


def update_metadata(session: ProjectSession, updates: Dict[str, Any]) -> Dict[str, Any]:
    metadata = _get_metadata(session)
    metadata.update(updates)
    session.metadata_json = metadata
    return metadata


def append_log(metadata: Dict[str, Any], step: str, message: str) -> None:
    logs = list(metadata.get("logs", []))
    logs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "step": step,
        "message": message
    })
    metadata["logs"] = logs


def _track_task(session_id: int, task: asyncio.Task) -> None:
    _running_tasks[session_id] = task
    task.add_done_callback(lambda t: _running_tasks.pop(session_id, None))


def _is_task_active(session_id: int) -> bool:
    task = _running_tasks.get(session_id)
    return bool(task and not task.done())


def _count_items(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def ensure_session_counts(session: Dict[str, Any]) -> None:
    results = session.get("pipeline_results") or {}
    session.setdefault("user_keywords", [])
    session.setdefault("extracted_keywords", [])
    session.setdefault("filters", {})
    session.setdefault("crawler_config", {})
    keywords = results.get("keywords") or session.get("extracted_keywords") or session.get("user_keywords") or []
    images = results.get("generated_images")
    design_count = 0
    model_count = 0
    if isinstance(images, list):
        for img in images:
            if not isinstance(img, dict):
                continue
            if "master_design" in img or "model_fittings" in img:
                if img.get("master_design"):
                    design_count += 1
                model_count += _count_items(img.get("model_fittings"))
                continue
            if img.get("type") == "model":
                model_count += 1
            else:
                design_count += 1
    blueprints = results.get("blueprints")
    blueprint_count = 0
    if isinstance(blueprints, list):
        if blueprints and isinstance(blueprints[0], dict) and any(k in blueprints[0] for k in ("sketch", "layout", "pattern")):
            for bp in blueprints:
                if not isinstance(bp, dict):
                    continue
                if bp.get("sketch"):
                    blueprint_count += 1
                if bp.get("layout"):
                    blueprint_count += 1
                if bp.get("pattern"):
                    blueprint_count += 1
        else:
            blueprint_count = len(blueprints)
    session["needs_count"] = _count_items(results.get("trends"))
    session["ideas_count"] = _count_items(results.get("design_ideas"))
    session["draft_count"] = blueprint_count
    session["crawled_count"] = _count_items(results.get("crawled_data"))
    session["keyword_count"] = _count_items(keywords)
    session["design_count"] = design_count
    session["model_image_count"] = model_count
    session["blueprint_count"] = blueprint_count


def serialize_session(session: ProjectSession) -> Dict[str, Any]:
    metadata = _get_metadata(session)
    session_data = {
        "id": session.id,
        "project_id": session.project_id,
        "session_title": session.name,
        "description": session.description or "",
        "user_keywords": metadata.get("user_keywords", []),
        "extracted_keywords": metadata.get("extracted_keywords", []),
        "filters": metadata.get("filters", {}),
        "crawler_config": metadata.get("crawler_config", {}),
        "input_text": metadata.get("input_text"),
        "input_urls": metadata.get("input_urls", []),
        "input_files": metadata.get("input_files", []),
        "auto_start": metadata.get("auto_start", True),
        "generate_images": metadata.get("generate_images", True),
        "generate_blueprints": metadata.get("generate_blueprints", False),
        "blueprint_size_system": metadata.get("blueprint_size_system", "KS"),
        "blueprint_size": metadata.get("blueprint_size", "M"),
        "status": metadata.get("status", "created"),
        "progress_percent": metadata.get("progress_percent", 0.0),
        "current_step": metadata.get("current_step"),
        "started_at": metadata.get("started_at"),
        "completed_at": metadata.get("completed_at"),
        "error_message": metadata.get("error_message"),
        "crawl_expected_items": metadata.get("crawl_expected_items", 0),
        "crawl_collected_items": metadata.get("crawl_collected_items", 0),
        "crawl_completed_keywords": metadata.get("crawl_completed_keywords", 0),
        "crawl_total_keywords": metadata.get("crawl_total_keywords", 0),
        "logs": metadata.get("logs", []),
        "pipeline_results": metadata.get("pipeline_results"),
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None
    }
    ensure_session_counts(session_data)
    return session_data


def get_session_record(db: Session, session_id: int) -> ProjectSession:
    session = db.query(ProjectSession).filter(ProjectSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def sync_session_state(db: Session, session: ProjectSession) -> ProjectSession:
    metadata = _get_metadata(session)
    status = metadata.get("status")
    if status in ("running", "analyzing") and not _is_task_active(session.id):
        metadata["status"] = "failed"
        metadata["current_step"] = "error"
        metadata["error_message"] = "워커 작업이 중단되었습니다. 다시 실행하세요."
        append_log(metadata, "error", "Failed: 워커 작업이 중단되었습니다. 다시 실행하세요.")
        session.metadata_json = metadata
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
    return session


def update_progress(session: ProjectSession, step: str, percent: float, message: str) -> None:
    metadata = _get_metadata(session)
    metadata["current_step"] = step
    metadata["progress_percent"] = round(percent, 1)
    append_log(metadata, step, message)
    session.metadata_json = metadata
    session.updated_at = datetime.utcnow()


def get_sessions_snapshot() -> List[Dict[str, Any]]:
    with get_db_session() as db:
        sessions = db.query(ProjectSession).all()
        sessions = [sync_session_state(db, session) for session in sessions]
        return [serialize_session(session) for session in sessions]


async def start_pipeline(session_id: int) -> None:
    with get_db_session() as db:
        session = get_session_record(db, session_id)
        project = db.query(Project).filter(Project.id == session.project_id).first()
        metadata = update_metadata(session, {
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "error_message": None,
            "progress_percent": 0.0
        })
        append_log(metadata, "started", "Pipeline started")
        session.metadata_json = metadata
        session.updated_at = datetime.utcnow()
        session_data = serialize_session(session)
        if project and project.preferred_image_model:
            session_data["preferred_image_model"] = project.preferred_image_model

    orchestrator = FashionPipelineOrchestrator()

    async def runner():
        try:
            def progress_cb(step: str, percent: float, message: str) -> None:
                with get_db_session() as progress_db:
                    progress_session = get_session_record(progress_db, session_id)
                    update_progress(progress_session, step, percent, message)

            def state_cb(updates: Dict[str, Any]) -> None:
                with get_db_session() as state_db:
                    state_session = get_session_record(state_db, session_id)
                    metadata = _get_metadata(state_session)
                    metadata.update(updates)
                    state_session.metadata_json = metadata
                    state_session.updated_at = datetime.utcnow()

            results = await orchestrator.run_complete_pipeline(session_data, progress_cb, state_cb)
            with get_db_session() as done_db:
                done_session = get_session_record(done_db, session_id)
                metadata = _get_metadata(done_session)
                report_payload = results.pop("report_payload", None)
                metadata["pipeline_results"] = results

                if not report_payload:
                    metadata["status"] = "failed"
                    metadata["error_message"] = "Report payload missing"
                    done_session.metadata_json = metadata
                    update_progress(
                        done_session,
                        "error",
                        metadata.get("progress_percent", 0.0),
                        "Failed: Report payload missing"
                    )
                    return

                report_service = ReportGenerationService()
                try:
                    report = report_service.upsert_report(done_db, session_data, report_payload)
                    metadata["report_name"] = report.report_name
                    metadata["report_language"] = report.language
                except Exception as report_exc:
                    metadata["status"] = "failed"
                    metadata["error_message"] = f"Report generation failed: {report_exc}"
                    done_session.metadata_json = metadata
                    update_progress(
                        done_session,
                        "error",
                        metadata.get("progress_percent", 0.0),
                        f"Failed: {report_exc}"
                    )
                    return

                metadata["status"] = "completed"
                metadata["completed_at"] = datetime.utcnow().isoformat()
                metadata["error_message"] = None
                done_session.metadata_json = metadata
                update_progress(done_session, "completed", 100, "Pipeline completed")
        except Exception as exc:
            logger.error(f"Pipeline failed: {exc}")
            with get_db_session() as fail_db:
                fail_session = get_session_record(fail_db, session_id)
                metadata = _get_metadata(fail_session)
                metadata["status"] = "failed"
                metadata["error_message"] = str(exc)
                fail_session.metadata_json = metadata
                update_progress(
                    fail_session,
                    "error",
                    metadata.get("progress_percent", 0.0),
                    f"Failed: {exc}"
                )

    task = asyncio.create_task(runner())
    _track_task(session_id, task)
