"""
자동 파이프라인 오케스트레이터.
레퍼런스 프로그램(Cosmetic_case_gen)의 PatentPipelineOrchestrator 패턴을 적용.

단계: brief_input → researching → concepting → referencing → abstracting → generating → documenting → review_ready
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.session import ChatMessage, DesignSession

logger = get_logger(__name__)

# @MX:ANCHOR: [AUTO] DesignPipelineOrchestrator — auto-mode pipeline driver
# @MX:REASON: Called by background task; all pipeline stages route through this class

STAGE_SEQUENCE = [
    "brief_input",
    "researching",
    "concepting",
    "referencing",
    "abstracting",
    "generating",
    "documenting",
    "review_ready",
]


class DesignPipelineOrchestrator:
    """
    전체 자동 파이프라인을 순서대로 실행한다.
    각 단계에서 pipeline_stage를 업데이트하고 auto_progress_log에 기록한다.
    """

    def __init__(self, session_id: uuid.UUID, db: Session, options: dict | None = None) -> None:
        self.session_id = session_id
        self.db = db
        self.options = options or {}

    async def run(self) -> None:
        """전체 파이프라인을 실행한다. 실패 시 pipeline_stage = 'failed'."""
        try:
            if self._enabled("research"):
                await self._step_researching()
            if self._enabled("concepts"):
                await self._step_concepting()
            if self._enabled("references"):
                await self._step_referencing()
            if self._enabled("abstraction"):
                await self._step_abstracting()
            if self._enabled("generation"):
                await self._step_generating()
            if self._enabled("spec"):
                await self._step_documenting()
            self._advance_stage("review_ready")
            logger.info("[PIPELINE] completed session=%s", self.session_id)
        except Exception as exc:
            logger.error("[PIPELINE] failed session=%s error=%s", self.session_id, exc)
            self._fail(str(exc))

    # ─── Stage: researching ───────────────────────────────────────────────────

    async def _step_researching(self) -> None:
        from app.application.use_cases.trends.search_trends import search_trends

        self._advance_stage("researching")
        session = self._get_session()
        brief = session.brief
        query = f"{brief.purpose} {brief.domain or ''} design trends".strip()

        started = _now()
        insights = await search_trends(self.db, self.session_id, query, brief.domain)
        evidence_urls = [i.document.url for i in insights if i.document and i.document.url]

        self._log_step("researching", started, len(insights), f"트렌드 {len(insights)}건 수집")
        self._add_progress_message(
            stage="researching",
            content=self._format_trend_summary(insights),
            evidence_links=evidence_urls,
        )

    # ─── Stage: concepting ───────────────────────────────────────────────────

    async def _step_concepting(self) -> None:
        from app.application.use_cases.concepts.generate_concepts import generate_concepts

        self._advance_stage("concepting")
        started = _now()
        candidates = await generate_concepts(self.db, self.session_id, allow_brief_only=True)

        if candidates:
            top = max(candidates, key=lambda c: c.score or 0)
            top.status = "adopted"
            self.db.commit()

        self._log_step("concepting", started, len(candidates), f"컨셉 후보 {len(candidates)}건 생성")
        self._add_progress_message(
            stage="concepting",
            content=self._format_concept_summary(candidates),
            evidence_links=[],
        )

    # ─── Stage: referencing ──────────────────────────────────────────────────

    async def _step_referencing(self) -> None:
        from app.application.use_cases.references.search_references import search_references

        self._advance_stage("referencing")
        session = self._get_session()
        brief = session.brief

        from app.models.concepts import ConceptCandidate
        adopted = (
            self.db.query(ConceptCandidate)
            .filter_by(session_id=self.session_id, status="adopted")
            .first()
        )
        query_parts = [brief.purpose, brief.domain or "", adopted.name if adopted else ""]
        query = " ".join(p for p in query_parts if p).strip()

        started = _now()
        assets = await search_references(self.db, self.session_id, query)
        evidence_urls = [a.url for a in assets if a.url]

        self._log_step("referencing", started, len(assets), f"레퍼런스 {len(assets)}건 수집")
        self._add_progress_message(
            stage="referencing",
            content=f"레퍼런스 {len(assets)}건이 수집되었습니다.\n" +
                    "\n".join(f"- {a.title or a.url}" for a in assets[:5]),
            evidence_links=evidence_urls,
        )

    # ─── Stage: abstracting ──────────────────────────────────────────────────

    async def _step_abstracting(self) -> None:
        from app.application.use_cases.references.search_references import analyze_reference
        from app.application.use_cases.abstraction.generate_abstraction import generate_abstraction
        from app.models.references import ReferenceAsset

        self._advance_stage("abstracting")
        assets = (
            self.db.query(ReferenceAsset)
            .filter_by(session_id=self.session_id, high_risk_blocked=False)
            .limit(3)
            .all()
        )

        started = _now()
        rules_generated = 0
        for asset in assets:
            try:
                await analyze_reference(self.db, asset.id)
                await generate_abstraction(self.db, self.session_id, "reference", asset.id)
                rules_generated += 1
            except Exception as exc:
                logger.warning("[PIPELINE] abstraction failed ref=%s: %s", asset.id, exc)

        self._log_step("abstracting", started, rules_generated, f"추상화 규칙 {rules_generated}건 생성")
        self._add_progress_message(
            stage="abstracting",
            content=f"레퍼런스 {len(assets)}건에서 추상화 규칙 {rules_generated}건을 도출했습니다.",
            evidence_links=[],
        )

    # ─── Stage: documenting ──────────────────────────────────────────────────

    async def _step_documenting(self) -> None:
        from app.application.use_cases.specs.generate_spec import generate_spec

        self._advance_stage("documenting")
        started = _now()
        spec = generate_spec(self.db, self.session_id)

        self._log_step("documenting", started, 1, f"스펙 문서 v{spec.version} 생성")
        self._add_progress_message(
            stage="documenting",
            content=f"스펙 문서 v{spec.version}이 생성되었습니다.\n"
                    f"검토 탭에서 전체 결과를 확인하세요.",
            evidence_links=[],
        )

    # ─── Stage: generating ───────────────────────────────────────────────────

    async def _step_generating(self) -> None:
        from app.application.use_cases.generation.create_generation_job import _build_prompt, _run_generation
        from app.models.abstraction import AbstractionRule
        from app.models.concepts import ConceptCandidate
        from app.models.generation import GeneratedDesign

        self._advance_stage("generating")
        session = self._get_session()
        brief_id = session.brief.id if session.brief else None
        concept = (
            self.db.query(ConceptCandidate)
            .filter_by(session_id=self.session_id, status="adopted")
            .first()
        )
        rules = (
            self.db.query(AbstractionRule)
            .filter_by(session_id=self.session_id)
            .order_by(AbstractionRule.created_at.asc())
            .limit(2)
            .all()
        )
        if not rules:
            raise ValueError("이미지 생성을 위한 추상화 규칙이 없습니다.")

        started = _now()
        designs = []
        for rule in rules:
            if rule.axes_count < 2:
                continue
            design = GeneratedDesign(
                session_id=self.session_id,
                rule_id=rule.id,
                brief_id=brief_id,
                concept_id=concept.id if concept else None,
                prompt=_build_prompt(rule),
                status="pending",
            )
            self.db.add(design)
            self.db.commit()
            self.db.refresh(design)
            await _run_generation(design.id)
            self.db.refresh(design)
            designs.append(design)

        completed = sum(1 for design in designs if design.status == "completed")
        if not designs:
            raise ValueError("이미지 생성 가능한 추상화 규칙이 없습니다.")
        self._log_step("generating", started, completed, f"이미지 {completed}/{len(designs)}건 생성")
        self._add_progress_message(
            stage="generating",
            content=f"최종 이미지 생성을 {len(designs)}건 시도했고 {completed}건 완료되었습니다.",
            evidence_links=[],
        )

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _get_session(self) -> DesignSession:
        session = self.db.get(DesignSession, self.session_id)
        if not session:
            raise ValueError(f"Session {self.session_id} not found")
        return session

    def _enabled(self, key: str) -> bool:
        return bool(self.options.get(key, True))

    def _advance_stage(self, stage: str) -> None:
        session = self._get_session()
        session.pipeline_stage = stage
        self.db.commit()
        logger.info("[PIPELINE] stage=%s session=%s", stage, self.session_id)

    def _log_step(self, stage: str, started: str, result_count: int, note: str) -> None:
        session = self._get_session()
        log = list(session.auto_progress_log or [])
        log.append({
            "stage": stage,
            "started_at": started,
            "completed_at": _now(),
            "result_count": result_count,
            "note": note,
        })
        session.auto_progress_log = log
        self.db.commit()

    def _add_progress_message(
        self, stage: str, content: str, evidence_links: list[str]
    ) -> None:
        msg = ChatMessage(
            session_id=self.session_id,
            role="assistant",
            content=content,
            stage=stage,
            evidence_links=evidence_links or None,
        )
        self.db.add(msg)
        self.db.commit()

    def _fail(self, error_msg: str) -> None:
        try:
            session = self._get_session()
            session.pipeline_stage = "failed"
            log = list(session.auto_progress_log or [])
            log.append({
                "stage": "failed",
                "started_at": _now(),
                "completed_at": _now(),
                "result_count": 0,
                "note": f"오류: {error_msg[:300]}",
            })
            session.auto_progress_log = log
            self.db.commit()
        except Exception as exc:
            logger.error("[PIPELINE] fail-handler error: %s", exc)

    @staticmethod
    def _format_trend_summary(insights: list) -> str:
        if not insights:
            return "트렌드 조사 결과가 없습니다. 검색 설정을 확인하거나 수동으로 검색하세요."
        lines = [f"트렌드 조사 완료: {len(insights)}건의 근거를 수집했습니다.\n"]
        for i, ins in enumerate(insights[:5], 1):
            lines.append(f"{i}. {ins.summary or ins.evidence_quote[:100]}")
        return "\n".join(lines)

    @staticmethod
    def _format_concept_summary(candidates: list) -> str:
        if not candidates:
            return "컨셉 후보를 생성하지 못했습니다. 트렌드 근거가 충분한지 확인하세요."
        adopted = [c for c in candidates if c.status == "adopted"]
        lines = [f"컨셉 후보 {len(candidates)}개가 생성되었습니다.\n"]
        if adopted:
            lines.append(f"자동 선택된 컨셉: **{adopted[0].name}**")
            lines.append(f"설명: {adopted[0].description or ''}")
        lines.append("\n다른 후보를 선택하려면 컨셉 탭에서 변경하세요.")
        return "\n".join(lines)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
