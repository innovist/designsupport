"""
Use-cases: search for reference assets and analyze individual references.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.infrastructure.search.image_search import get_image_search_client
from app.models.session import DesignSession
from app.models.references import ReferenceAnalysis, ReferenceAsset

logger = get_logger(__name__)

_COPYRIGHT_DOMAINS_HIGH_RISK = {"shutterstock.com", "gettyimages.com", "istockphoto.com"}

_ANALYSIS_PROMPT = """
Analyse this design reference image and return ONLY a JSON object:
{{
  "form_grammar": "description of dominant form patterns",
  "structure_grammar": "structural composition analysis",
  "material_direction": "material and texture clues",
  "meaning_symbols": "symbolic or semantic elements",
  "usability_notes": "ergonomic or UX observations",
  "replication_risk": "low | medium | high",
  "abstraction_fitness": 0.0-1.0
}}
"""


async def search_references(
    db: Session, session_id: uuid.UUID, query: str
) -> list[ReferenceAsset]:
    """Search images and store as ReferenceAsset rows. Returns empty list if no results."""
    if not db.get(DesignSession, session_id):
        raise ValueError(f"Session {session_id} not found")

    logger.info("[REFERENCE] searching session=%s query=%s", session_id, query[:100])
    search_client = get_image_search_client()
    results = await search_client.image_search(query, num_results=8)

    if not results:
        logger.info("[REFERENCE] no results session=%s query=%s", session_id, query[:100])
        return []

    assets: list[ReferenceAsset] = []
    for result in results:
        risk = _assess_copyright_risk(result.source_domain, result.url)
        asset = ReferenceAsset(
            session_id=session_id,
            asset_type="external",
            url=result.url,
            title=result.title,
            source_domain=result.source_domain,
            copyright_risk=risk,
            high_risk_blocked=(risk == "high"),
            collected_at=datetime.now(timezone.utc),
        )
        db.add(asset)
        assets.append(asset)

    db.commit()
    for a in assets:
        db.refresh(a)
    logger.info("[REFERENCE] stored session=%s count=%d query=%s", session_id, len(assets), query[:100])
    return assets


async def analyze_reference(db: Session, reference_id: uuid.UUID) -> ReferenceAnalysis:
    """Run AI analysis on a reference asset image."""
    asset = db.get(ReferenceAsset, reference_id)
    if not asset:
        raise ValueError(f"Reference {reference_id} not found")

    logger.info("[REFERENCE] analyzing reference_id=%s url=%s", reference_id, (asset.url or "")[:100])
    if asset.high_risk_blocked:
        raise PermissionError(
            f"Reference {reference_id} is blocked due to high copyright risk"
        )

    client = await get_ai_client(db, "reference_analysis")
    response = await client.vision_complete(
        messages=[AIMessage(role="user", content=_ANALYSIS_PROMPT)],
        image_paths=[asset.url] if asset.url else [],
        temperature=0.3,
        max_tokens=800,
    )

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed: dict = json.loads(raw)
    except Exception as parse_err:
        logger.warning("Reference analysis parse failed: %s", response.content[:200])
        raise ValueError(f"레퍼런스 분석 결과를 파싱할 수 없습니다: {parse_err}") from parse_err

    existing = db.query(ReferenceAnalysis).filter_by(reference_id=reference_id).first()
    if existing:
        for k, v in parsed.items():
            if hasattr(existing, k):
                setattr(existing, k, v)
        analysis = existing
    else:
        valid_keys = {c.key for c in ReferenceAnalysis.__table__.columns} - {"id", "reference_id"}
        analysis = ReferenceAnalysis(
            reference_id=reference_id,
            **{k: v for k, v in parsed.items() if k in valid_keys},
        )
        db.add(analysis)

    db.commit()
    db.refresh(analysis)
    logger.info("[REFERENCE] analysis done reference_id=%s risk=%s fitness=%s",
                reference_id, parsed.get("replication_risk"), parsed.get("abstraction_fitness"))
    return analysis


def update_reference_risk(
    db: Session, reference_id: uuid.UUID, copyright_risk: str, license_type: str | None
) -> ReferenceAsset:
    asset = db.get(ReferenceAsset, reference_id)
    if not asset:
        raise ValueError(f"Reference {reference_id} not found")

    asset.copyright_risk = copyright_risk
    asset.high_risk_blocked = copyright_risk == "high"
    if license_type:
        asset.license_type = license_type

    db.commit()
    db.refresh(asset)
    return asset


def _assess_copyright_risk(domain: str | None, url: str) -> str:
    if not domain:
        return "unknown"
    domain_lower = domain.lower()
    for high_risk in _COPYRIGHT_DOMAINS_HIGH_RISK:
        if high_risk in domain_lower:
            return "high"
    url_lower = url.lower()
    for term in ("premium", "stock", "licensed", "royalty"):
        if term in url_lower:
            return "medium"
    return "unknown"
