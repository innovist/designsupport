"""
Use-case: generate AbstractionRule from a reference analysis or sketch analysis.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.models.abstraction import AbstractionRule
from app.models.assets import SketchAnalysis, UserSketchAsset
from app.models.references import ReferenceAnalysis, ReferenceAsset

logger = get_logger(__name__)

_REF_ABSTRACTION_PROMPT = """
You are a design abstraction specialist. Based on the reference analysis below,
derive abstract design rules that guide new work WITHOUT replicating the original.

Reference Analysis:
Form: {form_grammar}
Structure: {structure_grammar}
Material: {material_direction}
Meaning: {meaning_symbols}
Usability: {usability_notes}

Return ONLY a JSON object:
{{
  "form": "abstract form principle (not a copy)",
  "structure": "abstract structural principle",
  "surface": "surface/texture direction",
  "color_material": "color/material direction",
  "meaning": "semantic/symbolic direction",
  "usability": "usability principle",
  "sketch_prompt": "prompt for sketch generation",
  "risk_notes": "replication or copyright risks to avoid"
}}
Ensure at least 2 distinct axes are populated (non-null).
"""

_SKETCH_ABSTRACTION_PROMPT = """
You are a design abstraction specialist. Based on the sketch analysis below,
derive rules for generating design variations.

Sketch Analysis:
Intent (hypothesis): {intent}
Form elements: {form_elements}
Structure elements: {structure_elements}
Keep elements: {keep_elements}
Vary elements: {vary_elements}

Return ONLY a JSON object:
{{
  "form": "abstract form principle",
  "structure": "structural direction",
  "surface": "surface/texture direction",
  "color_material": "color/material direction",
  "meaning": "semantic direction",
  "usability": "usability direction",
  "sketch_prompt": "image generation prompt for faithfully preserving intent",
  "keep_silhouette": "what silhouette to preserve",
  "strengthen_structure": "which structures to reinforce",
  "unclear_functions": "which functions need clarification",
  "refinement_directions": ["direction 1", "direction 2", "direction 3"],
  "preserve_prompt": "prompt emphasizing preservation",
  "expand_prompt": "prompt allowing exploration",
  "risk_notes": "risks to avoid"
}}
Ensure at least 2 distinct design axes are populated.
"""


async def generate_abstraction(
    db: Session,
    session_id: uuid.UUID,
    source_type: str,
    source_id: uuid.UUID,
) -> AbstractionRule:
    """
    Generate an AbstractionRule for the given source.

    source_type: 'reference' | 'sketch'
    source_id: UUID of ReferenceAsset or UserSketchAsset
    """
    if source_type not in ("reference", "sketch"):
        raise ValueError("source_type must be 'reference' or 'sketch'")

    client = await get_ai_client(db, "abstraction")

    if source_type == "reference":
        analysis = db.query(ReferenceAnalysis).filter_by(reference_id=source_id).first()
        if not analysis:
            raise ValueError(f"No ReferenceAnalysis for reference {source_id}")
        prompt = _REF_ABSTRACTION_PROMPT.format(
            form_grammar=analysis.form_grammar or "",
            structure_grammar=analysis.structure_grammar or "",
            material_direction=analysis.material_direction or "",
            meaning_symbols=analysis.meaning_symbols or "",
            usability_notes=analysis.usability_notes or "",
        )
    else:
        analysis = db.query(SketchAnalysis).filter_by(sketch_id=source_id).first()
        if not analysis:
            raise ValueError(f"No SketchAnalysis for sketch {source_id}")
        prompt = _SKETCH_ABSTRACTION_PROMPT.format(
            intent=analysis.intent or "",
            form_elements=analysis.form_elements or [],
            structure_elements=analysis.structure_elements or [],
            keep_elements=analysis.keep_elements or [],
            vary_elements=analysis.vary_elements or [],
        )

    response = await client.complete(
        [AIMessage(role="user", content=prompt)],
        temperature=0.4,
        max_tokens=1200,
    )

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed: dict = json.loads(raw)
    except Exception:
        logger.warning("Abstraction parse failed: %s", response.content[:300])
        raise ValueError("AI returned invalid abstraction JSON")

    # Count populated axes
    axis_keys = ("form", "structure", "surface", "color_material", "meaning", "usability")
    axes_count = sum(1 for k in axis_keys if parsed.get(k))

    if axes_count < 2:
        raise ValueError(
            f"Abstraction rule requires at least 2 design axes, got {axes_count}. "
            "Provide more analysis data."
        )

    valid_columns = {c.key for c in AbstractionRule.__table__.columns} - {
        "id", "session_id", "source_type", "source_id", "axes_count"
    }
    rule = AbstractionRule(
        session_id=session_id,
        source_type=source_type,
        source_id=source_id,
        axes_count=axes_count,
        **{k: v for k, v in parsed.items() if k in valid_columns},
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


async def generate_abstractions_for_session(
    db: Session,
    session_id: uuid.UUID,
    source_type: str,
) -> list[AbstractionRule]:
    """
    Generate AbstractionRules for all analyzed sources of source_type in the session.
    Sources without analysis are skipped.
    """
    if source_type == "reference":
        source_ids = [
            r.id
            for r in db.query(ReferenceAsset).filter_by(session_id=session_id).all()
            if db.query(ReferenceAnalysis).filter_by(reference_id=r.id).first() is not None
        ]
    elif source_type == "sketch":
        source_ids = [
            s.id
            for s in db.query(UserSketchAsset).filter_by(session_id=session_id, is_deleted=False).all()
            if db.query(SketchAnalysis).filter_by(sketch_id=s.id).first() is not None
        ]
    else:
        raise ValueError("source_type must be 'reference' or 'sketch'")

    if not source_ids:
        raise ValueError(
            f"No analyzed {source_type}s found in session. "
            "Analyze items first before generating abstraction rules."
        )

    rules = []
    for source_id in source_ids:
        rule = await generate_abstraction(db, session_id, source_type, source_id)
        rules.append(rule)
    return rules
