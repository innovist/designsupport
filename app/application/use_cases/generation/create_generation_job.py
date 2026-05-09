"""
Use-cases: create image generation job and retrieve generation result.
"""

from __future__ import annotations

import uuid

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.application.dtos.generation_dtos import GenerationRequest
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.models.abstraction import AbstractionRule
from app.models.generation import GeneratedDesign

logger = get_logger(__name__)


def create_generation_job(
    db: Session,
    session_id: uuid.UUID,
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
) -> GeneratedDesign:
    """
    Validate pre-conditions, create a GeneratedDesign record (status=pending),
    then enqueue the actual image generation as a background task.

    INVARIANT: rule_id must reference an existing AbstractionRule.
    """
    rule = db.get(AbstractionRule, request.rule_id)
    if not rule:
        raise ValueError(
            f"AbstractionRule {request.rule_id} not found. "
            "Generate abstraction rules before requesting image generation."
        )

    if rule.axes_count < 2:
        raise ValueError(
            f"AbstractionRule {request.rule_id} has only {rule.axes_count} axis/axes. "
            "Minimum 2 required for generation."
        )

    prompt = _build_prompt(rule)

    design = GeneratedDesign(
        session_id=session_id,
        rule_id=request.rule_id,
        brief_id=request.brief_id,
        concept_id=request.concept_id,
        prompt=prompt,
        status="pending",
        is_from_user_sketch=request.is_from_user_sketch,
    )
    db.add(design)
    db.commit()
    db.refresh(design)

    logger.info("[GENERATION] job created id=%s rule_id=%s session=%s", design.id, request.rule_id, session_id)
    background_tasks.add_task(_run_generation, design.id)
    return design


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
            client = await get_ai_client(bg_db, "image_generation")
            response = await client.generate_image(design.prompt)

            design.image_path = response.image_path
            design.provider = response.provider
            design.model = response.model
            design.status = "completed"
            logger.info("[GENERATION] completed id=%s provider=%s model=%s", design_id, response.provider, response.model)
        except Exception as exc:
            logger.error("[GENERATION] failed id=%s error=%s", design_id, exc)
            design.status = "failed"
            design.failure_reason = str(exc)

        bg_db.commit()


def get_generation_result(db: Session, generation_id: uuid.UUID) -> GeneratedDesign:
    design = db.get(GeneratedDesign, generation_id)
    if not design:
        raise ValueError(f"GeneratedDesign {generation_id} not found")
    return design


def _build_prompt(rule: AbstractionRule) -> str:
    """Compose an image generation prompt from the abstraction rule."""
    parts = []
    if rule.sketch_prompt:
        return rule.sketch_prompt
    for attr in ("form", "structure", "surface", "color_material", "meaning"):
        value = getattr(rule, attr)
        if value:
            parts.append(value)
    return ". ".join(parts) if parts else "Design sketch based on abstraction rules."
