"""
Use-cases: generate SpecDocument and version existing spec.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.infrastructure.repositories.session_repository import SessionRepository
from app.models.abstraction import AbstractionRule
from app.models.assets import UserSketchAsset
from app.models.concepts import ConceptCandidate, ConceptDecision
from app.models.generation import DesignEvaluation, GeneratedDesign
from app.models.references import ReferenceAsset
from app.models.specs import SpecDocument
from app.models.trends import TrendInsight

logger = get_logger(__name__)


# @MX:WARN: [AUTO] Complex data aggregation from 8+ tables with nested serialization
# @MX:REASON: High cyclomatic complexity (15+ branches) - single function touches entire domain model

def generate_spec(
    db: Session,
    session_id: uuid.UUID,
    selected_design_id: uuid.UUID | None = None,
) -> SpecDocument:
    """
    Collect all pipeline outputs and assemble a versioned SpecDocument.
    discarded_alternatives and decision_rationale are mandatory in content_json.
    """
    logger.info("[SPEC] generating session=%s", session_id)
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    brief = session.brief

    insights = (
        db.query(TrendInsight)
        .join(TrendInsight.document)
        .filter(TrendInsight.session_id == session_id)
        .limit(20)
        .all()
    )

    candidates = db.query(ConceptCandidate).filter_by(session_id=session_id).all()
    adopted = [c for c in candidates if c.status == "adopted"]
    discarded = [c for c in candidates if c.status == "discarded"]

    decisions = (
        db.query(ConceptDecision)
        .filter(ConceptDecision.candidate_id.in_([c.id for c in candidates]))
        .all()
    )

    sketches = (
        db.query(UserSketchAsset)
        .filter_by(session_id=session_id, is_deleted=False)
        .all()
    )

    references = db.query(ReferenceAsset).filter_by(session_id=session_id).all()

    rules = db.query(AbstractionRule).filter_by(session_id=session_id).all()

    designs = (
        db.query(GeneratedDesign)
        .filter_by(session_id=session_id, status="completed")
        .all()
    )
    selected_design = _resolve_selected_design(db, session_id, designs, selected_design_id)

    evaluations = db.query(DesignEvaluation).filter_by(session_id=session_id).all()

    content_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brief": _serialize_brief(brief),
        "trend_evidence": [_serialize_insight(i) for i in insights],
        "concept_candidates": [_serialize_candidate(c) for c in candidates],
        "final_concept": [_serialize_candidate(c) for c in adopted],
        "sketch_analysis": [_serialize_sketch(s) for s in sketches],
        "image_references": [_serialize_reference(r) for r in references if r.thumbnail_url],
        "abstraction_rules": [_serialize_rule(r) for r in rules],
        "generated_designs": [_serialize_design(d) for d in designs],
        "selected_design": _serialize_design(selected_design) if selected_design else None,
        "discarded_alternatives": [_serialize_discarded(c, decisions) for c in discarded],
        "decision_rationale": _build_decision_rationale(adopted, discarded, decisions),
        "sources": _trend_source_urls(insights),
        "design_evaluations": [_serialize_evaluation(e) for e in evaluations],
        "ai_usage_disclosure": {
            "trend_research": "AI-assisted web search and insight extraction",
            "concept_generation": "AI-generated candidates grounded in verified evidence",
            "abstraction": "AI-derived design rules from reference/sketch analysis",
            "generation": "AI sketch/final image generation from abstraction rules",
        },
    }

    existing = db.query(SpecDocument).filter_by(session_id=session_id).order_by(
        SpecDocument.version.desc()
    ).first()

    version = (existing.version + 1) if existing else 1
    parent_id = existing.id if existing else None

    spec = SpecDocument(
        session_id=session_id,
        version=version,
        content_json=content_json,
        status="draft",
        parent_version_id=parent_id,
        selected_design_id=selected_design.id if selected_design else None,
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    logger.info("[SPEC] v%d created session=%s insights=%d candidates=%d designs=%d",
                version, session_id, len(insights), len(candidates), len(designs))
    return spec


def version_spec(db: Session, spec_id: uuid.UUID) -> SpecDocument:
    """Create a new version of an existing spec."""
    existing = db.get(SpecDocument, spec_id)
    if not existing:
        raise ValueError(f"SpecDocument {spec_id} not found")
    return generate_spec(db, existing.session_id, existing.selected_design_id)


def _resolve_selected_design(
    db: Session,
    session_id: uuid.UUID,
    designs: list[GeneratedDesign],
    selected_design_id: uuid.UUID | None,
) -> GeneratedDesign | None:
    if selected_design_id:
        design = db.get(GeneratedDesign, selected_design_id)
        if (
            not design
            or design.session_id != session_id
            or design.status != "completed"
            or not design.image_path
        ):
            raise ValueError("보고서 기준 이미지는 이 세션의 작성 완료된 생성 이미지여야 합니다.")
        return design

    completed_with_image = [d for d in designs if d.image_path]
    if not completed_with_image:
        return None

    finals = [
        d for d in completed_with_image
        if (d.generation_params or {}).get("output_kind") in {"final", "final_image"}
    ]
    if finals:
        return max(finals, key=lambda d: d.created_at)
    return max(completed_with_image, key=lambda d: d.created_at)


# --- serializers ---

def _serialize_brief(brief) -> dict:
    if not brief:
        return {}
    return {
        "purpose": brief.purpose,
        "domain": brief.domain,
        "target_user": brief.target_user,
        "context": brief.context,
        "constraints": brief.constraints,
        "use_case": brief.use_case,
        "result_form": brief.result_form,
    }


def _serialize_insight(i: TrendInsight) -> dict:
    return {
        "id": str(i.id),
        "title": i.title,
        "summary": i.summary,
        "keywords": i.keywords or [],
        "source_urls": i.source_urls or [],
    }


def _serialize_candidate(c: ConceptCandidate) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "description": c.description,
        "score": c.score,
        "rationale": c.rationale,
        "risk": c.risk,
        "status": c.status,
    }


def _serialize_sketch(s: UserSketchAsset) -> dict:
    result: dict = {"id": str(s.id), "filename": s.original_filename}
    if s.analysis:
        result["analysis"] = {
            "intent": s.analysis.intent,
            "form_elements": s.analysis.form_elements,
            "user_confirmed": s.analysis.user_confirmed,
        }
    return result


def _serialize_reference(r: ReferenceAsset) -> dict:
    return {
        "id": str(r.id),
        "title": r.title,
        "url": r.url,
        "thumbnail_url": r.thumbnail_url,
        "copyright_risk": r.copyright_risk,
        "high_risk_blocked": r.high_risk_blocked,
    }


def _serialize_rule(r: AbstractionRule) -> dict:
    return {
        "id": str(r.id),
        "source_type": r.source_type,
        "form": r.form,
        "structure": r.structure,
        "surface": r.surface,
        "color_material": r.color_material,
        "meaning": r.meaning,
        "usability": r.usability,
        "axes_count": r.axes_count,
        "sketch_prompt": r.sketch_prompt,
    }


def _serialize_design(d: GeneratedDesign) -> dict:
    return {
        "id": str(d.id),
        "image_path": d.image_path,
        "image_url": d.image_url,
        "prompt": d.prompt,
        "provider": d.provider,
        "model": d.model,
        "output_kind": (d.generation_params or {}).get("output_kind"),
    }


def _trend_source_urls(insights: list[TrendInsight]) -> list[str]:
    urls: list[str] = []
    for insight in insights:
        for item in insight.source_urls or []:
            url = item.get("url") if isinstance(item, dict) else item
            if isinstance(url, str) and url and url not in urls:
                urls.append(url)
        document_url = insight.document.url if insight.document else None
        if document_url and document_url not in urls:
            urls.append(document_url)
    return urls


def _serialize_discarded(c: ConceptCandidate, decisions: list[ConceptDecision]) -> dict:
    decision = next((d for d in decisions if d.candidate_id == c.id), None)
    return {
        "id": str(c.id),
        "name": c.name,
        "reason": decision.reason if decision else None,
    }


def _serialize_evaluation(e: DesignEvaluation) -> dict:
    return {
        "id": str(e.id),
        "winner_id": str(e.winner_id) if e.winner_id else None,
        "scores": e.scores,
        "notes": e.notes,
        "discarded_with_reason": e.discarded_with_reason,
    }


def _build_decision_rationale(
    adopted: list[ConceptCandidate],
    discarded: list[ConceptCandidate],
    decisions: list[ConceptDecision],
) -> dict:
    return {
        "adopted_count": len(adopted),
        "discarded_count": len(discarded),
        "selection_criteria": "Score, rationale strength, and verified trend evidence",
        "adopted_concepts": [c.name for c in adopted],
        "decisions": [
            {"candidate": d.candidate_id and str(d.candidate_id), "decision": d.decision, "reason": d.reason}
            for d in decisions
        ],
    }
