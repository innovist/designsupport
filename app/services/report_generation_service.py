"""
Report generation service for trend analysis
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model, get_glm_model
from app.models.report import Report, ReportStatus, ReportFormat
from app.services.pipeline_utils import parse_json
from ai_clients.gemini_client import get_gemini_client
from ai_clients.glm_client import GLMClient

logger = get_logger(__name__)
settings = get_settings()

REPORT_TYPE_TREND = "trend_analysis"
REQUIRED_REPORT_KEYS = (
    "title",
    "executive_summary",
    "target_audience",
    "research_scope",
    "market_analysis",
    "trend_analysis",
    "competitor_analysis",
    "design_proposals",
    "recommendations",
    "conclusion",
)

LANGUAGE_LABELS = {
    "ko": "Korean",
    "en": "English",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Traditional Chinese",
}


def build_report_name(session_id: int) -> str:
    return f"session_{session_id}"


def _language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)


def _trim_text(text: str, limit: int) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _source_stats(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    stats: Dict[str, int] = {}
    comment_total = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or item.get("platform") or "unknown"
        stats[source] = stats.get(source, 0) + 1
        metadata = item.get("metadata") or {}
        comments = metadata.get("comments") or []
        if isinstance(comments, list):
            comment_total += len(comments)
    return {
        "source_counts": stats,
        "comment_total": comment_total,
        "total_items": sum(stats.values())
    }


def _sample_items(items: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    samples = []
    for item in items:
        if not isinstance(item, dict):
            continue
        samples.append({
            "title": item.get("title"),
            "source": item.get("source"),
            "published_at": item.get("published_at"),
            "url": item.get("url"),
            "snippet": _trim_text(item.get("content") or "", 220)
        })
        if len(samples) >= limit:
            break
    return samples


def _normalize_design_proposals(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


class ReportGenerationService:
    """Generate report payloads for trend analysis."""

    def __init__(self) -> None:
        self.client = get_gemini_client()
        self.glm_client = GLMClient()

    def _resolve_language(self, session_data: Dict[str, Any]) -> str:
        language = session_data.get("language") or settings.default_language
        return language if settings.validate_language(language) else settings.default_language

    def build_context(
        self,
        session_data: Dict[str, Any],
        crawled: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        ideas: List[Dict[str, Any]],
        keywords: List[str]
    ) -> Dict[str, Any]:
        return {
            "session": {
                "id": session_data.get("id"),
                "project_id": session_data.get("project_id"),
                "title": session_data.get("session_title"),
                "description": session_data.get("description"),
                "filters": session_data.get("filters") or {},
                "crawler_config": session_data.get("crawler_config") or {},
                "keywords": keywords
            },
            "data_stats": _source_stats(crawled),
            "sample_items": _sample_items(crawled),
            "analysis": {
                "summary": analysis.get("summary"),
                "key_trends": analysis.get("key_trends"),
                "market_insights": analysis.get("market_insights"),
                "recommendations": analysis.get("recommendations"),
                "comment_insights": analysis.get("comment_insights"),
                "confidence_score": analysis.get("confidence_score")
            },
            "design_ideas": ideas
        }

    async def _repair_payload(self, raw_text: str, language: str) -> str:
        system_prompt = (
            "You are a JSON formatter. Convert the input into a strict JSON object. "
            "Do not add extra keys beyond the required set. If a field is missing, "
            "use an empty string or an empty array. "
            f"Respond in {language}. Required keys: {', '.join(REQUIRED_REPORT_KEYS)}."
        )
        response = await self.glm_client.generate_content(
            prompt=raw_text,
            model=get_glm_model(),
            system_prompt=system_prompt
        )
        if not response or not response.text:
            raise ValueError("Report payload repair response is empty")
        return response.text

    async def _parse_payload(self, text: str, language: str) -> Dict[str, Any]:
        try:
            return parse_json(text)
        except Exception as exc:
            logger.warning(f"Report payload JSON parse failed, attempting repair: {exc}")
            repaired = await self._repair_payload(text, language)
            return parse_json(repaired)

    async def generate_payload(
        self,
        session_data: Dict[str, Any],
        crawled: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        ideas: List[Dict[str, Any]],
        keywords: List[str]
    ) -> Dict[str, Any]:
        context = self.build_context(session_data, crawled, analysis, ideas, keywords)
        language = _language_label(self._resolve_language(session_data))
        system_instruction = (
            "You are a fashion trend research analyst. Use only the provided context JSON. "
            "Do not invent sources, brands, or statistics. If data is missing, return empty strings "
            "or empty arrays for those fields. "
            f"Respond in {language}. "
            "Output strict JSON with keys: title, executive_summary, target_audience, research_scope, "
            "market_analysis, trend_analysis, competitor_analysis, design_proposals, recommendations, conclusion."
        )
        prompt = json.dumps(context, ensure_ascii=False)

        try:
            response = await self.client.generate_content(
                prompt=prompt,
                model=get_gemini_model(),
                system_instruction=system_instruction
            )
        except Exception as exc:
            logger.warning(f"Gemini report generation failed, falling back to GLM: {exc}")
            response = await self.glm_client.generate_content(
                prompt=prompt,
                model=get_glm_model(),
                system_prompt=system_instruction
            )

        if not response or not response.text:
            raise ValueError("Report payload response is empty")

        data = await self._parse_payload(response.text, language)
        if not isinstance(data, dict):
            raise ValueError("Report payload is not a JSON object")

        missing = set(REQUIRED_REPORT_KEYS) - set(data.keys())
        if missing:
            raise ValueError(f"Missing report payload keys: {sorted(missing)}")

        logger.info("Report payload generated")
        return data

    def upsert_report(
        self,
        db: Any,
        session_data: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> Report:
        session_id = session_data.get("id")
        project_id = session_data.get("project_id")
        if session_id is None or project_id is None:
            raise ValueError("Session id/project id required for report")

        language = self._resolve_language(session_data)
        report_name = build_report_name(int(session_id))

        report = db.query(Report).filter(
            Report.project_id == project_id,
            Report.report_type == REPORT_TYPE_TREND,
            Report.report_name == report_name,
            Report.language == language,
        ).order_by(Report.created_at.desc()).first()

        if report is None:
            report = Report(
                project_id=project_id,
                report_name=report_name,
                report_type=REPORT_TYPE_TREND,
                status=ReportStatus.DRAFT,
                language=language,
                format=ReportFormat.MARKDOWN,
            )
            db.add(report)

        report.status = ReportStatus.COMPLETED
        report.title = _normalize_text(payload.get("title"))
        report.executive_summary = _normalize_text(payload.get("executive_summary"))
        report.target_audience = _normalize_text(payload.get("target_audience"))
        report.research_scope = _normalize_text(payload.get("research_scope"))
        report.market_analysis = _normalize_text(payload.get("market_analysis"))
        report.trend_analysis = _normalize_text(payload.get("trend_analysis"))
        report.competitor_analysis = _normalize_text(payload.get("competitor_analysis"))
        report.design_proposals = _normalize_design_proposals(payload.get("design_proposals"))
        report.recommendations = _normalize_text(payload.get("recommendations"))
        report.conclusion = _normalize_text(payload.get("conclusion"))
        report.generated_at = datetime.utcnow()
        report.update_counts()
        return report
