"""
Use-cases: generate concept candidates and record decisions.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.infrastructure.repositories.session_repository import SessionRepository
from app.models.concepts import ConceptCandidate, ConceptDecision
from app.models.trends import TrendInsight

logger = get_logger(__name__)

_CONCEPT_PROMPT = """
You are a design concept strategist. Given the design brief and trend evidence below,
generate 3 to 5 distinct concept candidates.

IMPORTANT: All textual fields (name, description, rationale, risk) MUST be written in Korean (한국어).
Only field keys remain in English.

Design Brief:
{brief_text}

Trend Evidence (verified facts only - is_hypothesis=false):
{trend_evidence}

Return ONLY a JSON array of objects, each with:
{{
  "name": "컨셉 이름 (한국어)",
  "description": "2-3 문장 설명 (한국어)",
  "score": 0.0-1.0,
  "rationale": "이 컨셉이 브리프와 근거에 부합하는 이유 (한국어)",
  "risk": "잠재적 위험 또는 한계 (한국어)",
  "trend_evidence": [{{ "source": "url", "quote": "direct quote" }}]
}}
"""

_CONCEPT_BRIEF_ONLY_PROMPT = """
You are a design concept strategist. No trend data is available, so generate concepts
based solely on the design brief using your domain expertise.

IMPORTANT: All textual fields (name, description, rationale, risk) MUST be written in Korean (한국어).
Only field keys remain in English.

Design Brief:
{brief_text}

Return ONLY a JSON array of 3 objects, each with:
{{
  "name": "컨셉 이름 (한국어)",
  "description": "2-3 문장 설명 (한국어)",
  "score": 0.0-1.0,
  "rationale": "이 컨셉이 브리프에 부합하는 이유 (한국어)",
  "risk": "잠재적 위험 또는 한계 (한국어)",
  "trend_evidence": []
}}
"""


# @MX:ANCHOR: [AUTO] Concept generation called by pipeline and manual triggers
# @MX:REASON: Business-critical AI feature - validates brief completeness and grounds concepts in verified evidence

async def generate_concepts(
    db: Session, session_id: uuid.UUID, allow_brief_only: bool = False
) -> list[ConceptCandidate]:
    """Generate concept candidates grounded in verified trend insights.

    When allow_brief_only=True and no verified insights exist, falls back to
    brief-only concept generation (used by auto pipeline when search is not configured).
    """
    repo = SessionRepository(db)
    session = repo.get_by_id(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    brief = session.brief
    if not brief or not brief.is_complete:
        raise ValueError("Brief must be complete before generating concepts")

    # Only use verified (non-hypothesis) trend insights as evidence
    verified_insights = (
        db.query(TrendInsight)
        .join(TrendInsight.document)
        .filter(TrendInsight.session_id == session_id)
        .filter(TrendInsight.is_hypothesis == False)  # noqa: E712
        .limit(10)
        .all()
    )

    brief_text = (
        f"Purpose: {brief.purpose}\n"
        f"Domain: {brief.domain}\n"
        f"Target user: {brief.target_user}\n"
        f"Result form: {brief.result_form}"
    )

    if not verified_insights and not allow_brief_only:
        raise ValueError(
            "Verified trend evidence is required before generating concept candidates. "
            "Run trend search and keep only sourced insights first."
        )

    logger.info("[CONCEPT] generating session=%s evidence_count=%d", session_id, len(verified_insights))
    client = await get_ai_client(db, "concept_generation")

    if verified_insights:
        trend_text = "\n".join(
            f"- {i.evidence_quote} (source: {i.document.url})"
            for i in verified_insights
        )
        prompt = _CONCEPT_PROMPT.format(brief_text=brief_text, trend_evidence=trend_text)
    else:
        logger.warning("[CONCEPT] no verified insights; using brief-only prompt session=%s", session_id)
        prompt = _CONCEPT_BRIEF_ONLY_PROMPT.format(brief_text=brief_text)

    response = await client.complete(
        [AIMessage(role="user", content=prompt)],
        temperature=0.7,
        max_tokens=2000,
    )

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        candidates_data: list[dict] = json.loads(raw)
    except Exception:
        logger.warning("Concept generation parse failed: %s", response.content[:300])
        raise ValueError("AI returned invalid JSON for concept candidates")

    evidence_ids = [str(i.id) for i in verified_insights]
    candidates: list[ConceptCandidate] = []
    for data in candidates_data:
        candidate = ConceptCandidate(
            session_id=session_id,
            name=data.get("name", "Unnamed"),
            description=data.get("description"),
            score=data.get("score"),
            rationale=data.get("rationale"),
            risk=data.get("risk"),
            evidence_ids=evidence_ids,
            trend_evidence=data.get("trend_evidence", []),
            generated_by="ai",
            status="pending",
        )
        db.add(candidate)
        candidates.append(candidate)

    db.commit()
    for c in candidates:
        db.refresh(c)
    logger.info("[CONCEPT] generated session=%s candidates=%d", session_id, len(candidates))
    return candidates


def record_concept_decision(
    db: Session,
    candidate_id: uuid.UUID,
    decision: str,
    reason: str | None = None,
) -> ConceptDecision:
    """Record user decision for a concept candidate and update its status."""
    valid_decisions = {"adopt", "hold", "discard", "explore"}
    if decision not in valid_decisions:
        raise ValueError(f"Invalid decision '{decision}'. Valid: {sorted(valid_decisions)}")

    candidate = db.get(ConceptCandidate, candidate_id)
    if not candidate:
        raise ValueError(f"Concept candidate {candidate_id} not found")

    status_map = {"adopt": "adopted", "hold": "held", "discard": "discarded", "explore": "pending"}
    candidate.status = status_map[decision]

    concept_decision = ConceptDecision(
        candidate_id=candidate_id,
        decision=decision,
        decider="user",
        reason=reason,
    )
    db.add(concept_decision)
    db.commit()
    db.refresh(concept_decision)
    return concept_decision
