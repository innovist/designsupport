"""
Use-case: save an uploaded sketch file and record the asset.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.assets import UserSketchAsset

logger = get_logger(__name__)
settings = get_settings()


async def upload_sketch(
    db: Session, session_id: uuid.UUID, file: UploadFile, memo: str | None = None
) -> UserSketchAsset:
    """Persist uploaded sketch and return the asset record."""
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise ValueError(f"File too large: {size_mb:.1f} MB (max {settings.max_file_size_mb} MB)")

    dest_dir = Path(settings.upload_dir) / "sketches" / str(session_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}_{file.filename or 'sketch'}"
    dest_path = dest_dir / filename
    dest_path.write_bytes(content)

    asset = UserSketchAsset(
        session_id=session_id,
        file_path=str(dest_path),
        original_filename=file.filename,
        file_size=len(content),
        mime_type=file.content_type,
        user_memo=memo,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    logger.info("Sketch uploaded: %s", asset.id)
    return asset
