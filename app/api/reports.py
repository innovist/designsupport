"""Report API endpoints"""
from datetime import datetime
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.core.settings_storage import get_gemini_model, get_glm_model
from app.models.report import Report, ReportStatus, ReportFormat
from app.services.pipeline_utils import parse_json
from ai_clients.gemini_client import get_gemini_client
from ai_clients.glm_client import GLMClient
router = APIRouter()
settings = get_settings()
TRANSLATABLE_FIELDS = (
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
def _language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)
def _ensure_language(language: Optional[str]) -> str:
    target = language or settings.default_language
    if not settings.validate_language(target):
        raise HTTPException(status_code=400, detail=f"Unsupported language: {target}")
    return target
def _parse_design_proposals(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value
def _serialize_report(report: Report) -> Dict[str, Any]:
    return {
        "id": report.id,
        "project_id": report.project_id,
        "report_name": report.report_name,
        "report_type": report.report_type,
        "status": report.status.value if isinstance(report.status, ReportStatus) else str(report.status),
        "language": report.language,
        "title": report.title,
        "executive_summary": report.executive_summary,
        "target_audience": report.target_audience,
        "research_scope": report.research_scope,
        "market_analysis": report.market_analysis,
        "trend_analysis": report.trend_analysis,
        "competitor_analysis": report.competitor_analysis,
        "design_proposals": report.design_proposals,
        "recommendations": report.recommendations,
        "conclusion": report.conclusion,
        "word_count": report.word_count,
        "character_count": report.character_count,
        "file_path": report.file_path,
        "file_url": report.file_url,
        "format": report.format.value if isinstance(report.format, ReportFormat) else str(report.format),
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }
def _find_report(
    db: Session,
    project_id: int,
    report_type: str,
    report_name: Optional[str],
    language: Optional[str] = None,
) -> Optional[Report]:
    query = db.query(Report).filter(
        Report.project_id == project_id,
        Report.report_type == report_type,
    )
    if report_name:
        query = query.filter(Report.report_name == report_name)
    if language:
        query = query.filter(Report.language == language)
    return query.order_by(Report.created_at.desc()).first()
def _build_translation_payload(report: Report) -> Dict[str, Any]:
    payload = {field: getattr(report, field) for field in TRANSLATABLE_FIELDS}
    payload["design_proposals"] = _parse_design_proposals(report.design_proposals)
    return payload
async def _translate_payload(
    payload: Dict[str, Any],
    source_language: str,
    target_language: str
) -> Dict[str, Any]:
    if not payload:
        return payload

    system_instruction = (
        f"You are a professional translator. Translate JSON values from "
        f"{_language_label(source_language)} to {_language_label(target_language)}. "
        "Keep all keys and JSON structure unchanged. Do not add or remove keys. "
        "Preserve nulls, numbers, and booleans. Translate only string values."
    )
    prompt = json.dumps(payload, ensure_ascii=False)
    client = get_gemini_client()
    try:
        response = await client.generate_content(
            prompt=prompt,
            model=get_gemini_model(),
            system_instruction=system_instruction
        )
    except Exception:
        glm_client = GLMClient()
        response = await glm_client.generate_content(
            prompt=prompt,
            model=get_glm_model(),
            system_prompt=system_instruction
        )
    if not response or not response.text:
        raise ValueError("Empty translation response")

    try:
        translated = parse_json(response.text)
    except Exception:
        translated = await _repair_translation_json(response.text, payload.keys())
    if set(translated.keys()) != set(payload.keys()):
        raise ValueError("Translated JSON keys mismatch")
    return translated
async def _repair_translation_json(text: str, keys: Any) -> Dict[str, Any]:
    formatter = GLMClient()
    repair_prompt = (
        "You are a JSON formatter. Fix the input into strict JSON. "
        "Keep all keys and JSON structure unchanged. Do not add or remove keys. "
        f"Required keys: {', '.join(keys)}."
    )
    repaired = await formatter.generate_content(
        prompt=text,
        model=get_glm_model(),
        system_prompt=repair_prompt
    )
    if not repaired or not repaired.text:
        raise ValueError("Empty translation response")
    return parse_json(repaired.text)
def _normalize_design_proposals(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
def _normalize_text_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
def _build_translated_report(report: Report, translated: Dict[str, Any], target_language: str) -> Report:
    translated_design = _normalize_design_proposals(translated.get("design_proposals"))
    new_report = Report(
        project_id=report.project_id,
        report_name=report.report_name,
        report_type=report.report_type,
        status=report.status,
        language=target_language,
        title=_normalize_text_value(translated.get("title")),
        executive_summary=_normalize_text_value(translated.get("executive_summary")),
        target_audience=_normalize_text_value(translated.get("target_audience")),
        research_scope=_normalize_text_value(translated.get("research_scope")),
        market_analysis=_normalize_text_value(translated.get("market_analysis")),
        trend_analysis=_normalize_text_value(translated.get("trend_analysis")),
        competitor_analysis=_normalize_text_value(translated.get("competitor_analysis")),
        design_proposals=translated_design,
        recommendations=_normalize_text_value(translated.get("recommendations")),
        conclusion=_normalize_text_value(translated.get("conclusion")),
        format=report.format,
        generated_at=report.generated_at or datetime.utcnow(),
        file_path=None,
        file_url=None,
    )
    new_report.update_counts()
    return new_report


def _apply_translation(
    report: Report,
    translated: Dict[str, Any],
    target_language: str,
    source_generated_at: Optional[datetime]
) -> Report:
    translated_design = _normalize_design_proposals(translated.get("design_proposals"))
    report.language = target_language
    report.title = _normalize_text_value(translated.get("title"))
    report.executive_summary = _normalize_text_value(translated.get("executive_summary"))
    report.target_audience = _normalize_text_value(translated.get("target_audience"))
    report.research_scope = _normalize_text_value(translated.get("research_scope"))
    report.market_analysis = _normalize_text_value(translated.get("market_analysis"))
    report.trend_analysis = _normalize_text_value(translated.get("trend_analysis"))
    report.competitor_analysis = _normalize_text_value(translated.get("competitor_analysis"))
    report.design_proposals = translated_design
    report.recommendations = _normalize_text_value(translated.get("recommendations"))
    report.conclusion = _normalize_text_value(translated.get("conclusion"))
    report.generated_at = source_generated_at or datetime.utcnow()
    report.update_counts()
    return report


async def _get_or_translate_report(
    db: Session,
    report: Report,
    target_language: str
) -> Report:
    existing = _find_report(
        db,
        report.project_id,
        report.report_type,
        report.report_name,
        target_language
    )
    if existing:
        if report.generated_at and existing.generated_at:
            if existing.generated_at >= report.generated_at:
                return existing
        elif not report.generated_at:
            return existing

    payload = _build_translation_payload(report)
    try:
        translated = await _translate_payload(payload, report.language, target_language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report translation failed: {exc}") from exc
    if existing:
        updated = _apply_translation(existing, translated, target_language, report.generated_at)
        db.add(updated)
        db.commit()
        db.refresh(updated)
        return updated
    translated_report = _build_translated_report(report, translated, target_language)
    db.add(translated_report)
    db.commit()
    db.refresh(translated_report)
    return translated_report


@router.get("/")
async def get_report_by_project(
    project_id: int = Query(..., description="Project ID"),
    report_type: str = Query(..., description="Report type"),
    report_name: Optional[str] = Query(None, description="Report name filter"),
    language: Optional[str] = Query(None, description="Target language"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    target_language = _ensure_language(language)
    report = _find_report(db, project_id, report_type, report_name, target_language)
    if report:
        return _serialize_report(report)

    source = _find_report(db, project_id, report_type, report_name, None)
    if not source:
        raise HTTPException(status_code=404, detail="Report not found")
    if source.language == target_language:
        return _serialize_report(source)

    translated = await _get_or_translate_report(db, source, target_language)
    return _serialize_report(translated)


@router.get("/{report_id}")
async def get_report_by_id(
    report_id: int,
    language: Optional[str] = Query(None, description="Target language"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    target_language = _ensure_language(language)
    if report.language == target_language:
        return _serialize_report(report)

    translated = await _get_or_translate_report(db, report, target_language)
    return _serialize_report(translated)
