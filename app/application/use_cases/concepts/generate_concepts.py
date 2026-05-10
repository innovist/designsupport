"""
Use-cases: generate concept candidates and record decisions.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.application.use_cases.trends.insight_text import format_insight_for_prompt
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.infrastructure.repositories.session_repository import SessionRepository
from app.models.concepts import ConceptCandidate, ConceptDecision
from app.models.trends import TrendInsight
from app.utils.json_parse import parse_json_array

logger = get_logger(__name__)

_CONCEPT_PROMPT = """
You are a visual design concept specialist. Your role is to generate distinct VISUAL DESIGN CONCEPTS — not product features, not technology specs, not business models.

A visual design concept defines: how the design LOOKS, how it FEELS, and what visual language it speaks.
Each concept must address at least one of: Form Language, Color Direction, Material/Texture, Mood/Atmosphere, or Visual Metaphor.

STRICTLY FORBIDDEN in descriptions or rationale:
- Product features or functions (e.g. "smart sensor integration", "AI capabilities")
- Technology specifications (e.g. "app connectivity", "IoT platform")
- Business or service models (e.g. "subscription tier", "B2B solution")
- Market, sales, operational, or UX workflow claims unless they are directly visible in the design form

CORRECT visual concept examples:
- "유기적 곡선과 내추럴 소재의 조화 — 부드러운 형태언어와 무광 소재 대비"
- "미니멀리즘 + 금속 텍스처 대비 — 절제된 형태에 산업적 표면 마감"
- "레트로 미래주의 조형 언어 — 기하학적 볼륨과 크롬 반사 효과"

Write every concept as a DESIGN DIRECTION that a designer can sketch:
- name: short visual title, not a product slogan
- description: visible shape, proportion, material, surface, color, line, silhouette, composition
- rationale: why this visual language fits the brief and trend evidence
- risk: visual/production design risk only, not business risk

IMPORTANT: All textual fields (name, description, rationale, risk) MUST be written in Korean (한국어).
Only field keys remain in English.

Design Brief:
{brief_text}

Trend Evidence (verified facts only — use as visual inspiration, not feature ideas):
{trend_evidence}

Return ONLY a JSON array of 3 to 5 objects, each with:
{{
  "name": "시각적 컨셉 이름 — 조형/색채/소재 언어를 담은 이름 (한국어)",
  "description": "이 디자인이 어떻게 보이고 어떤 느낌인지 — 형태언어·색상 방향·소재·분위기·시각적 은유 중 하나 이상을 포함한 2-3문장 (한국어)",
  "score": 0.0-1.0,
  "rationale": "이 시각적 방향이 브리프의 목적/타겟/맥락에 부합하는 이유, 트렌드 근거와의 연결 (한국어)",
  "risk": "이 시각적 접근의 잠재적 한계 또는 실현 난이도 (한국어)",
  "trend_evidence": [{{ "source": "url", "quote": "direct quote" }}]
}}
"""

_CONCEPT_BRIEF_ONLY_PROMPT = """
You are a visual design concept specialist. Your role is to generate distinct VISUAL DESIGN CONCEPTS — not product features, not technology specs, not business models.

A visual design concept defines: how the design LOOKS, how it FEELS, and what visual language it speaks.
Each concept must address at least one of: Form Language, Color Direction, Material/Texture, Mood/Atmosphere, or Visual Metaphor.

STRICTLY FORBIDDEN in descriptions or rationale:
- Product features or functions (e.g. "smart sensor integration", "AI capabilities")
- Technology specifications (e.g. "app connectivity", "IoT platform")
- Business or service models (e.g. "subscription tier", "B2B solution")
- Market, sales, operational, or UX workflow claims unless they are directly visible in the design form

CORRECT visual concept examples:
- "유기적 곡선과 내추럴 소재의 조화 — 부드러운 형태언어와 무광 소재 대비"
- "미니멀리즘 + 금속 텍스처 대비 — 절제된 형태에 산업적 표면 마감"
- "레트로 미래주의 조형 언어 — 기하학적 볼륨과 크롬 반사 효과"

Write every concept as a DESIGN DIRECTION that a designer can sketch:
- name: short visual title, not a product slogan
- description: visible shape, proportion, material, surface, color, line, silhouette, composition
- rationale: why this visual language fits the brief
- risk: visual/production design risk only, not business risk

IMPORTANT: All textual fields (name, description, rationale, risk) MUST be written in Korean (한국어).
Only field keys remain in English.

Design Brief:
{brief_text}

Return ONLY a JSON array of 3 objects, each with:
{{
  "name": "시각적 컨셉 이름 — 조형/색채/소재 언어를 담은 이름 (한국어)",
  "description": "이 디자인이 어떻게 보이고 어떤 느낌인지 — 형태언어·색상 방향·소재·분위기·시각적 은유 중 하나 이상을 포함한 2-3문장 (한국어)",
  "score": 0.0-1.0,
  "rationale": "이 시각적 방향이 브리프의 목적/타겟/맥락에 부합하는 이유 (한국어)",
  "risk": "이 시각적 접근의 잠재적 한계 또는 실현 난이도 (한국어)",
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
        evidence_lines = [
            line for insight in verified_insights
            if (line := format_insight_for_prompt(insight))
        ]
        if not evidence_lines:
            raise ValueError("Verified trend evidence has no usable summary or source text.")
        trend_text = "\n".join(evidence_lines)
        prompt = _CONCEPT_PROMPT.format(brief_text=brief_text, trend_evidence=trend_text)
    else:
        logger.warning("[CONCEPT] no verified insights; using brief-only prompt session=%s", session_id)
        prompt = _CONCEPT_BRIEF_ONLY_PROMPT.format(brief_text=brief_text)

    response = await client.complete(
        [AIMessage(role="user", content=prompt)],
        temperature=0.7,
        max_tokens=4000,
    )

    try:
        candidates_data = parse_json_array(response.content, required_key="name")
    except Exception:
        logger.warning("Concept generation parse failed: %s", response.content[:400])
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
