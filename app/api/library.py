"""
Library API for Fashion AI Generation System
Provides access to generated images with filtering and pagination
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.logging import get_logger
from app.api.sessions import get_sessions_snapshot
from app.api.projects import get_projects_snapshot

router = APIRouter()
logger = get_logger(__name__)


class ImageItem(BaseModel):
    """Generated image item"""
    id: str
    url: str
    path: Optional[str] = None
    filename: str
    title: str
    type: str  # 'design' | 'model' | 'blueprint'
    prompt: Optional[str] = None
    session_id: int
    session_title: str
    project_id: int
    project_name: str
    created_at: str


class LibraryResponse(BaseModel):
    """Library API response"""
    images: List[ImageItem]
    total: int
    page: int
    limit: int
    stats: Dict[str, int]


def _extract_images_from_sessions(sessions: List[Dict]) -> List[Dict]:
    """Extract all images from session results"""
    all_images = []
    projects = get_projects_snapshot()
    project_map = {p.get("id"): p for p in projects}

    for session in sessions:
        session_id = session.get("id", 0)
        session_title = session.get("session_title", "Unknown")
        project_id = session.get("project_id", 0)

        project = project_map.get(project_id)
        project_name = project.get("title", "Unknown") if project else "Unknown"

        results = session.get("pipeline_results", {})
        if not results:
            continue

        # Extract generated images (design & model)
        generated_images = results.get("generated_images", [])
        flat_images = []
        for img in generated_images:
            if isinstance(img, dict) and ("master_design" in img or "model_fittings" in img):
                idea = img.get("idea") or {}
                base_title = idea.get("concept_name") or idea.get("concept") or idea.get("title") or "Design"
                master = img.get("master_design")
                if isinstance(master, dict):
                    master["type"] = master.get("type") or "design"
                    master["title"] = master.get("title") or f"{base_title} - Design"
                    master["prompt"] = master.get("prompt") or idea.get("prompt") or ""
                    flat_images.append(master)
                for idx, model in enumerate(img.get("model_fittings") or []):
                    if not isinstance(model, dict):
                        continue
                    model["type"] = model.get("type") or "model"
                    model["title"] = model.get("title") or f"{base_title} - Model {idx + 1}"
                    model["prompt"] = model.get("prompt") or idea.get("prompt") or ""
                    flat_images.append(model)
            else:
                flat_images.append(img)
        for idx, img in enumerate(flat_images):
            if not isinstance(img, dict):
                continue
            img_type = img.get("type", "design")
            data_url = img.get("url") or _data_url(img.get("image_base64"), img.get("mime_type"))
            all_images.append({
                "id": f"img_{session_id}_{idx}",
                "url": data_url or img.get("path", ""),
                "path": img.get("path", ""),
                "filename": img.get("filename", f"image_{idx}.png"),
                "title": img.get("title", img.get("description", f"Image {idx + 1}")),
                "type": img_type,
                "prompt": img.get("prompt", ""),
                "session_id": session_id,
                "session_title": session_title,
                "project_id": project_id,
                "project_name": project_name,
                "created_at": img.get("created_at", session.get("completed_at", ""))
            })

        # Extract blueprints
        blueprints = results.get("blueprints", [])
        flat_blueprints = []
        for bp in blueprints:
            if isinstance(bp, dict) and any(k in bp for k in ("sketch", "layout", "pattern")):
                idea = bp.get("idea") or {}
                base_title = idea.get("concept_name") or idea.get("concept") or idea.get("title") or "Blueprint"
                for key in ("sketch", "layout", "pattern"):
                    item = bp.get(key)
                    if not isinstance(item, dict):
                        continue
                    item["type"] = item.get("type") or key
                    item["title"] = item.get("title") or f"{base_title} - {key.title()}"
                    flat_blueprints.append(item)
            else:
                flat_blueprints.append(bp)
        for idx, bp in enumerate(flat_blueprints):
            if not isinstance(bp, dict):
                continue
            data_url = bp.get("url") or _data_url(bp.get("image_base64"), bp.get("mime_type"))
            all_images.append({
                "id": f"bp_{session_id}_{idx}",
                "url": data_url or bp.get("path", ""),
                "path": bp.get("path", ""),
                "filename": bp.get("filename", f"blueprint_{idx}.png"),
                "title": bp.get("title", f"Blueprint {idx + 1}"),
                "type": "blueprint",
                "prompt": "",
                "session_id": session_id,
                "session_title": session_title,
                "project_id": project_id,
                "project_name": project_name,
                "created_at": bp.get("created_at", session.get("completed_at", ""))
            })

    return all_images

def _data_url(image_base64: Optional[str], mime_type: Optional[str]) -> str:
    if not image_base64:
        return ""
    mime = mime_type or "image/jpeg"
    return f"data:{mime};base64,{image_base64}"


def _filter_images(
    images: List[Dict],
    project_id: Optional[int],
    session_id: Optional[int],
    image_type: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str]
) -> List[Dict]:
    """Apply filters to images"""
    filtered = images

    if project_id:
        filtered = [img for img in filtered if img.get("project_id") == project_id]

    if session_id:
        filtered = [img for img in filtered if img.get("session_id") == session_id]

    if image_type:
        filtered = [img for img in filtered if img.get("type") == image_type]

    if date_from:
        filtered = [img for img in filtered
                    if img.get("created_at", "") >= date_from]

    if date_to:
        filtered = [img for img in filtered
                    if img.get("created_at", "")[:10] <= date_to]

    return filtered


def _sort_images(images: List[Dict], sort: str) -> List[Dict]:
    """Sort images"""
    if sort == "created_at_asc":
        return sorted(images, key=lambda x: x.get("created_at", ""))
    elif sort == "name_asc":
        return sorted(images, key=lambda x: x.get("title", "").lower())
    else:  # created_at_desc (default)
        return sorted(images, key=lambda x: x.get("created_at", ""), reverse=True)


def _calculate_stats(images: List[Dict]) -> Dict[str, int]:
    """Calculate image statistics"""
    stats = {
        "total": len(images),
        "design": 0,
        "model": 0,
        "blueprint": 0
    }

    for img in images:
        img_type = img.get("type", "")
        if img_type in stats:
            stats[img_type] += 1

    return stats


@router.get("", response_model=LibraryResponse)
async def get_library(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    session_id: Optional[int] = Query(None, description="Filter by session"),
    image_type: Optional[str] = Query(None, description="Filter by type"),
    date_from: Optional[str] = Query(None, description="Filter from date"),
    date_to: Optional[str] = Query(None, description="Filter to date"),
    sort: str = Query("created_at_desc", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(24, ge=1, le=100, description="Items per page")
) -> Dict[str, Any]:
    """
    Get library images with filtering and pagination

    - **project_id**: Filter by project ID
    - **session_id**: Filter by session ID
    - **image_type**: Filter by type (design, model, blueprint)
    - **date_from**: Filter from date (YYYY-MM-DD)
    - **date_to**: Filter to date (YYYY-MM-DD)
    - **sort**: Sort order (created_at_desc, created_at_asc, name_asc)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 24, max: 100)
    """
    try:
        # Get all sessions
        sessions = get_sessions_snapshot()

        # Extract all images from completed sessions
        completed_sessions = [s for s in sessions if s.get("status") == "completed"]
        all_images = _extract_images_from_sessions(completed_sessions)

        # Apply filters
        filtered_images = _filter_images(
            all_images, project_id, session_id, image_type, date_from, date_to
        )

        # Calculate stats before pagination
        stats = _calculate_stats(filtered_images)

        # Sort
        sorted_images = _sort_images(filtered_images, sort)

        # Paginate
        total = len(sorted_images)
        start = (page - 1) * limit
        end = start + limit
        paginated_images = sorted_images[start:end]

        return {
            "images": paginated_images,
            "total": total,
            "page": page,
            "limit": limit,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get library: {e}")
        return {
            "images": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "stats": {"total": 0, "design": 0, "model": 0, "blueprint": 0}
        }


@router.get("/stats")
async def get_library_stats() -> Dict[str, Any]:
    """Get library statistics"""
    try:
        sessions = get_sessions_snapshot()
        completed_sessions = [s for s in sessions if s.get("status") == "completed"]
        all_images = _extract_images_from_sessions(completed_sessions)
        stats = _calculate_stats(all_images)

        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get library stats: {e}")
        return {
            "success": False,
            "stats": {"total": 0, "design": 0, "model": 0, "blueprint": 0}
        }
