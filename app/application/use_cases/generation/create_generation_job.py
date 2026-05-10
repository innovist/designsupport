"""
Use-cases: create image generation job and retrieve generation result.
"""

from __future__ import annotations

import uuid
import base64
import re
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.application.dtos.generation_dtos import GenerationRequest
from app.application.use_cases.generation.build_generation_prompt import (
    DRAFT_OUTPUT,
    build_generation_prompt,
    image_feature_for_output,
    normalize_output_kind,
)
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.models.abstraction import AbstractionRule
from app.models.concepts import ConceptCandidate
from app.models.generation import GeneratedDesign

logger = get_logger(__name__)


async def create_generation_job(
    db: Session,
    session_id: uuid.UUID,
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
) -> GeneratedDesign:
    """
    Validate pre-conditions, create a GeneratedDesign record (status=pending),
    then enqueue the actual image generation as a background task.

    Drafts require a selected concept. Abstraction rule is optional because
    users may generate drafts before abstraction rules exist.
    """
    output_kind = normalize_output_kind(request.output_kind)
    source_draft = (
        _validate_final_generation_source(db, session_id, request)
        if output_kind == "final"
        else None
    )
    concept_id = request.concept_id or (source_draft.concept_id if source_draft else None)
    if output_kind == DRAFT_OUTPUT:
        _validate_draft_concept(db, session_id, concept_id)

    rule_id = request.rule_id or (source_draft.rule_id if source_draft else None)
    rule = _get_optional_rule(db, session_id, rule_id)

    if rule and rule.axes_count < 2:
        raise ValueError(
            f"AbstractionRule {rule.id} has only {rule.axes_count} axis/axes. "
            "Minimum 2 required for generation."
        )

    prompt = await build_generation_prompt(
        db,
        rule,
        output_kind,
        concept_id,
        feedback_note=request.feedback_note,
    )

    design = GeneratedDesign(
        session_id=session_id,
        rule_id=rule_id,
        brief_id=request.brief_id,
        concept_id=concept_id,
        prompt=prompt,
        status="pending",
        generation_params={
            "output_kind": output_kind,
            "source_draft_id": str(request.source_draft_id) if request.source_draft_id else None,
            "source_draft_image_path": source_draft.image_path if source_draft else None,
            "feedback_note": request.feedback_note,
        },
        is_from_user_sketch=request.is_from_user_sketch,
    )
    db.add(design)
    db.commit()
    db.refresh(design)

    logger.info("[GENERATION] job created id=%s rule_id=%s concept_id=%s session=%s", design.id, rule_id, concept_id, session_id)
    background_tasks.add_task(_run_generation, design.id)
    return design


def _get_optional_rule(
    db: Session,
    session_id: uuid.UUID,
    rule_id: uuid.UUID | None,
) -> AbstractionRule | None:
    if not rule_id:
        return None
    rule = db.get(AbstractionRule, rule_id)
    if not rule or rule.session_id != session_id:
        raise ValueError("추상화 규칙을 찾을 수 없습니다.")
    return rule


def _validate_draft_concept(
    db: Session,
    session_id: uuid.UUID,
    concept_id: uuid.UUID | None,
) -> None:
    if not concept_id:
        raise ValueError("초안 생성에는 컨셉 선택이 필요합니다.")
    concept = db.get(ConceptCandidate, concept_id)
    if not concept or concept.session_id != session_id:
        raise ValueError("선택한 컨셉을 찾을 수 없습니다.")


async def _run_generation(design_id: uuid.UUID) -> None:
    """Background task: call image generation API and update the record."""
    from app.core.database import SessionLocal

    with SessionLocal() as bg_db:
        design = bg_db.get(GeneratedDesign, design_id)
        if not design:
            return

        logger.info("[GENERATION] starting id=%s", design_id)
        design.status = "processing"
        bg_db.commit()

        try:
            output_kind = _output_kind_for_design(design)
            client = await get_ai_client(bg_db, image_feature_for_output(output_kind))
            response = await client.generate_image(
                design.prompt,
                reference_image_paths=_reference_image_paths_for_design(design),
            )

            design.image_path = _persist_generated_image(design.id, response.image_path)
            design.provider = response.provider
            design.model = response.model
            design.status = "completed"
            bg_db.commit()
            logger.info("[GENERATION] completed id=%s provider=%s model=%s", design_id, response.provider, response.model)
        except Exception as exc:
            bg_db.rollback()
            logger.error("[GENERATION] failed id=%s error=%s", design_id, exc)
            design = bg_db.get(GeneratedDesign, design_id)
            if not design:
                return
            design.status = "failed"
            design.failure_reason = str(exc)
            bg_db.commit()


def get_generation_result(db: Session, generation_id: uuid.UUID) -> GeneratedDesign:
    design = db.get(GeneratedDesign, generation_id)
    if not design:
        raise ValueError(f"GeneratedDesign {generation_id} not found")
    return design


def retry_generation_job(
    db: Session,
    generation_id: uuid.UUID,
    background_tasks: BackgroundTasks,
) -> GeneratedDesign:
    """Reset a failed generation and run it again with the current model settings."""
    design = get_generation_result(db, generation_id)
    if design.status not in {"failed"}:
        raise ValueError("실패한 생성 결과만 다시 생성할 수 있습니다.")
    if not design.prompt:
        raise ValueError("재생성할 프롬프트가 없습니다.")

    design.status = "pending"
    design.failure_reason = None
    design.provider = None
    design.model = None
    design.image_path = None
    params = dict(design.generation_params or {})
    params["retry_of"] = str(design.id)
    design.generation_params = params
    db.commit()
    db.refresh(design)

    background_tasks.add_task(_run_generation, design.id)
    logger.info("[GENERATION] retry queued id=%s", design.id)
    return design


def _output_kind_for_design(design: GeneratedDesign) -> str:
    params = design.generation_params or {}
    kind = params.get("output_kind") or DRAFT_OUTPUT
    return normalize_output_kind(kind)


def _validate_final_generation_source(
    db: Session,
    session_id: uuid.UUID,
    request: GenerationRequest,
) -> GeneratedDesign:
    if not request.source_draft_id:
        raise ValueError("최종안 생성에는 기반 초안이 필요합니다.")
    if not request.feedback_note or not request.feedback_note.strip():
        raise ValueError("최종안 생성에는 사용자 검토 의견이 필요합니다.")

    source_draft = db.get(GeneratedDesign, request.source_draft_id)
    if not source_draft or source_draft.session_id != session_id:
        raise ValueError("기반 초안을 찾을 수 없습니다.")
    if _output_kind_for_design(source_draft) != DRAFT_OUTPUT:
        raise ValueError("최종안의 기반 이미지는 완료된 초안이어야 합니다.")
    if source_draft.status != "completed" or not source_draft.image_path:
        raise ValueError("완료된 초안 이미지만 최종안 생성에 사용할 수 있습니다.")
    if request.rule_id and source_draft.rule_id and source_draft.rule_id != request.rule_id:
        raise ValueError("기반 초안과 추상화 규칙이 일치하지 않습니다.")
    return source_draft


def _reference_image_paths_for_design(design: GeneratedDesign) -> list[str]:
    if _output_kind_for_design(design) != "final":
        return []

    params = design.generation_params or {}
    image_path = params.get("source_draft_image_path")
    if not image_path or image_path.startswith(("http://", "https://", "data:")):
        return []
    if image_path.startswith("/uploads/"):
        image_path = image_path.removeprefix("/uploads/")

    path = Path(image_path)
    if path.is_absolute():
        return [str(path)]
    return [str(Path(get_settings().upload_dir) / image_path.lstrip("/"))]


def _persist_generated_image(design_id: uuid.UUID, image_path: str) -> str:
    if not image_path.startswith("data:image/"):
        return image_path

    match = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", image_path, re.DOTALL)
    if not match:
        return image_path

    mime_type, encoded = match.groups()
    extension = _extension_for_mime_type(mime_type)
    upload_root = Path(get_settings().upload_dir)
    output_dir = upload_root / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{design_id}.{extension}"
    (output_dir / filename).write_bytes(base64.b64decode(encoded))
    return f"generated/{filename}"


def _extension_for_mime_type(mime_type: str) -> str:
    if mime_type == "image/jpeg":
        return "jpg"
    if mime_type == "image/webp":
        return "webp"
    return "png"
