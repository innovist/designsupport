"""
Use-case: search for trend insights relevant to a session brief.
Collects multiple web sources, synthesizes them into 5 trend insights via AI.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.infrastructure.repositories.trend_repository import TrendRepository
from app.infrastructure.repositories.workspace_repository import WorkspaceRepository
from app.infrastructure.search.web_search import get_search_client
from app.models.session import DesignSession
from app.models.trends import TrendDocument, TrendInsight, TrendSource
from app.utils.json_parse import parse_json_array

logger = get_logger(__name__)

_SYNTHESIS_PROMPT = """다음 참고자료들을 종합하여 [{query}] 관련 디자인 트렌드를 5가지로 분석하라.

참고자료:
{sources}

각 트렌드 항목:
- title: 트렌드 이름 (10~20자, 한국어)
- summary: 2~3문장으로 트렌드 설명 (한국어, 구체적이고 실용적으로)
- keywords: 관련 키워드 3~5개 (한국어)
- domain_tags: 영문 도메인 태그 1~3개 (예: "material", "form", "color", "technology")
- source_indices: 이 트렌드를 뒷받침하는 참고자료 번호 목록 (0-based 정수 배열)
- confidence_score: 0.0~1.0 (참고자료 근거 충분도)

JSON 배열만 반환하라. 다른 텍스트 없이:
[
  {{
    "title": "...",
    "summary": "...",
    "keywords": ["...", "..."],
    "domain_tags": ["..."],
    "source_indices": [0, 1],
    "confidence_score": 0.8
  }},
  ...
]"""


async def search_trends(
    db: Session, session_id: uuid.UUID, query: str, domain: str | None = None
) -> list[TrendInsight]:
    """
    Search web for trend sources, synthesize into up to 5 trend insights.
    Returns stored TrendInsight rows (may be empty if search fails).
    """
    session = db.get(DesignSession, session_id)
    if not session:
        logger.warning("[TREND] session not found session=%s", session_id)
        return []

    workspace_repo = WorkspaceRepository(db)
    trend_repo = TrendRepository(db)
    workspace = session.project.workspace if session.project else workspace_repo.ensure_default_workspace()
    trend_setting = workspace_repo.get_trend_setting(workspace.id)
    trend_sources, enforce_host_filter = _resolve_trend_sources(trend_repo, trend_setting)
    allowed_hosts = _source_hosts(trend_sources) if enforce_host_filter else set()

    search_query = _build_search_query(
        query,
        domain or (trend_setting.default_domain if trend_setting else None),
    )
    logger.info(
        "[TREND] searching session=%s query=%s source_count=%d",
        session_id,
        search_query[:120],
        len(trend_sources),
    )

    search_client = get_search_client()
    results = await search_client.web_search(search_query, num_results=8)
    if allowed_hosts:
        filtered = [result for result in results if _url_host(result.url) in allowed_hosts]
        if filtered:
            results = filtered
        else:
            logger.warning(
                "[TREND] search filtered all results from allowed source hosts session=%s hosts=%s",
                session_id,
                sorted(allowed_hosts),
            )

    if not results:
        logger.info("[TREND] no results session=%s query=%s", session_id, search_query[:100])
        return []

    ai_client = await get_ai_client(db, "trend_analysis")

    # Store TrendDocuments for all collected sources
    docs: list[TrendDocument] = []
    for result in results:
        content_hash = hashlib.sha256(result.url.encode()).hexdigest()
        existing = trend_repo.get_document_by_hash(content_hash)
        if existing:
            docs.append(existing)
            continue

        source = _find_matching_source(trend_sources, result.url)
        if source is None:
            source = _get_or_create_search_source(db, "web_search")
        doc = TrendDocument(
            source_id=source.id,
            title=result.title,
            url=result.url,
            collected_at=datetime.now(timezone.utc),
            parsed_text=result.snippet,
            content_hash=content_hash,
        )
        db.add(doc)
        docs.append(doc)
    db.flush()

    # Build source context for AI synthesis
    source_lines = []
    for idx, (result, doc) in enumerate(zip(results, docs)):
        snippet = (result.snippet or "")[:400]
        source_lines.append(f"[{idx}] 제목: {result.title}\n    URL: {result.url}\n    내용: {snippet}")
    sources_text = "\n\n".join(source_lines)

    try:
        ai_response = await ai_client.complete(
            [AIMessage(role="user", content=_SYNTHESIS_PROMPT.format(query=query, sources=sources_text))],
            temperature=0.4,
            max_tokens=2000,
        )
        trend_items = parse_json_array(ai_response.content)
    except Exception as exc:
        logger.error("[TREND] synthesis failed session=%s: %s", session_id, exc)
        return []

    insights: list[TrendInsight] = []
    anchor_doc = docs[0]

    for item in trend_items[:5]:
        source_indices: list[int] = item.get("source_indices", [])
        source_urls = [
            {"url": docs[i].url, "title": docs[i].title or docs[i].url}
            for i in source_indices
            if 0 <= i < len(docs)
        ]

        insight = TrendInsight(
            document_id=anchor_doc.id,
            session_id=session_id,
            title=item.get("title"),
            summary=item.get("summary"),
            keywords=item.get("keywords", []),
            domain_tags=item.get("domain_tags", []),
            evidence_quote=None,
            confidence_score=float(item.get("confidence_score", 0.7)),
            is_hypothesis=False,
            source_urls=source_urls,
        )
        db.add(insight)
        insights.append(insight)

    db.commit()
    for i in insights:
        if i.id:
            db.refresh(i)

    logger.info(
        "[TREND] stored session=%s insights=%d results=%d query=%s",
        session_id,
        len(insights),
        len(results),
        search_query[:100],
    )
    return insights


def _build_search_query(query: str, domain: str | None) -> str:
    parts: list[str] = [part for part in (query or "").strip().split() if part]
    if domain and domain not in parts:
        parts.append(domain)
    parts.append("design")
    parts.append("trends")
    return " ".join(dict.fromkeys(parts))


def _resolve_trend_sources(
    trend_repo: TrendRepository, trend_setting: object | None
) -> tuple[list[TrendSource], bool]:
    if not trend_setting or not getattr(trend_setting, "enabled_source_ids", None):
        return [], False

    enabled_source_ids = getattr(trend_setting, "enabled_source_ids", None)
    if not isinstance(enabled_source_ids, list):
        return [], False

    sources = trend_repo.get_sources_by_ids([str(item) for item in enabled_source_ids if item])
    return sources, bool(sources)


def _source_hosts(sources: list[TrendSource]) -> set[str]:
    hosts: set[str] = set()
    for source in sources:
        host = _url_host(source.url or "")
        if host:
            hosts.add(host)
    return hosts


def _url_host(raw_url: str) -> str:
    host = urlparse(raw_url).hostname or ""
    return host.lower().removeprefix("www.")


def _find_matching_source(sources: list[TrendSource], raw_url: str) -> TrendSource | None:
    result_host = _url_host(raw_url)
    if not result_host:
        return None
    for source in sources:
        source_host = _url_host(source.url or "")
        if not source_host:
            continue
        if result_host == source_host or result_host.endswith("." + source_host) or source_host.endswith("." + result_host):
            return source
    return None


def _get_or_create_search_source(db: Session, name: str) -> TrendSource:
    source = db.query(TrendSource).filter_by(name=name).first()
    if not source:
        source = TrendSource(name=name, is_active=True)
        db.add(source)
        db.flush()
    return source
