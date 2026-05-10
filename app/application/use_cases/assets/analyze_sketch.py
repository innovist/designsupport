"""
Use-cases: AI sketch analysis and user confirmation.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.models.assets import SketchAnalysis, UserSketchAsset
from app.utils.json_parse import parse_json_object

logger = get_logger(__name__)

_ANALYSIS_PROMPT = """
You are a design analysis AI. Analyse the uploaded sketch image and return ONLY a JSON object with:
{
  "intent": "string - your hypothesis of what the designer is trying to create",
  "form_elements": ["list of identified form elements"],
  "structure_elements": ["list of structural elements"],
  "unclear_points": ["list of ambiguous or unclear elements"],
  "questions_for_user": ["1-3 clarifying questions"],
  "keep_elements": ["elements to preserve in refinement"],
  "vary_elements": ["elements that could be varied"]
}
intent_is_hypothesis is always true until user confirms.
"""


async def analyze_sketch(db: Session, sketch_id: uuid.UUID) -> SketchAnalysis:
    """Request AI analysis for a sketch. Creates or replaces existing analysis."""
    sketch = db.get(UserSketchAsset, sketch_id)
    if not sketch or sketch.is_deleted:
        raise ValueError(f"Sketch {sketch_id} not found")

    logger.info("[SKETCH] analyzing sketch_id=%s file=%s", sketch_id, sketch.file_path)
    client = await get_ai_client(db, "sketch_analysis")
    response = await client.vision_complete(
        messages=[AIMessage(role="user", content=_ANALYSIS_PROMPT)],
        image_paths=[sketch.file_path],
        temperature=0.4,
        max_tokens=1500,
    )

    try:
        parsed = parse_json_object(response.content)
    except Exception as parse_err:
        logger.warning("Sketch analysis JSON parse failed: %s", response.content[:200])
        raise ValueError(f"스케치 분석 결과를 파싱할 수 없습니다. AI 응답 형식 오류: {parse_err}") from parse_err

    existing = db.query(SketchAnalysis).filter_by(sketch_id=sketch_id).first()
    if existing:
        for k, v in parsed.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        existing.intent_is_hypothesis = True
        existing.user_confirmed = False
        analysis = existing
        logger.info("[SKETCH] analysis updated sketch_id=%s intent=%s", sketch_id, parsed.get("intent", "")[:80])
    else:
        analysis = SketchAnalysis(
            sketch_id=sketch_id,
            intent_is_hypothesis=True,
            user_confirmed=False,
            **{k: v for k, v in parsed.items() if k in SketchAnalysis.__table__.columns},
        )
        db.add(analysis)
        logger.info("[SKETCH] analysis created sketch_id=%s intent=%s", sketch_id, parsed.get("intent", "")[:80])

    db.commit()
    db.refresh(analysis)
    return analysis


def confirm_sketch_analysis(
    db: Session,
    sketch_id: uuid.UUID,
    confirmed: bool,
    corrections: dict | None = None,
) -> SketchAnalysis:
    """User confirms or corrects AI sketch analysis."""
    analysis = db.query(SketchAnalysis).filter_by(sketch_id=sketch_id).first()
    if not analysis:
        raise ValueError(f"No analysis found for sketch {sketch_id}")

    analysis.user_confirmed = confirmed
    if corrections:
        analysis.user_corrections = corrections
        for k, v in corrections.items():
            if hasattr(analysis, k):
                setattr(analysis, k, v)
    # intent_is_hypothesis becomes False only when user confirmed without major corrections
    if confirmed and not corrections:
        analysis.intent_is_hypothesis = False

    db.commit()
    db.refresh(analysis)
    logger.info("[SKETCH] user confirmed sketch_id=%s confirmed=%s has_corrections=%s",
                sketch_id, confirmed, bool(corrections))
    return analysis
