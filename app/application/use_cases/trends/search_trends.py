"""
Use-case: search for trend insights relevant to a session brief.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.core.logging import get_logger
from app.infrastructure.ai_clients.factory import get_ai_client
from app.infrastructure.repositories.trend_repository import TrendRepository
from app.infrastructure.search.web_search import get_search_client
from app.models.trends import TrendDocument, TrendInsight, TrendSource

logger = get_logger(__name__)

_INSIGHT_PROMPT = """
Extract design trend insights from the following article text.
Return ONLY a JSON object:
{{
  "summary": "one paragraph summary relevant to {query}",
  "keywords": ["keyword1", "keyword2"],
  "domain_tags": ["domain1"],
  "evidence_quote": "direct quote from the text that supports the insight (required)",
  "confidence_score": 0.0-1.0,
  "is_hypothesis": false
}}
If no clear evidence quote exists, set is_hypothesis to true and use the best sentence as evidence_quote.

Article:
{text}
"""


async def search_trends(
    db: Session, session_id: uuid.UUID, query: str, domain: str | None = None
) -> list[TrendInsight]:
    """
    Search for trends matching query, store TrendDocument + TrendInsight rows.
    Returns the list of stored insights (may be empty if no results found - never mocked).
    """
    import json

    search_query = f"{query} {domain}" if domain else query
    logger.info("[TREND] searching session=%s query=%s", session_id, search_query[:100])
    search_client = get_search_client()
    results = await search_client.web_search(search_query, num_results=5)

    if not results:
        logger.info("[TREND] no results session=%s query=%s", session_id, search_query[:100])
        return []

    trend_repo = TrendRepository(db)
    ai_client = await get_ai_client(db, "trend_analysis")

    stored_source = _get_or_create_search_source(db, "web_search")
    insights: list[TrendInsight] = []

    for result in results:
        content_hash = hashlib.sha256(result.url.encode()).hexdigest()
        existing_doc = trend_repo.get_document_by_hash(content_hash)
        if existing_doc:
            existing_insights = [
                insight
                for insight in existing_doc.insights
                if insight.session_id == session_id
            ]
            if existing_insights:
                insights.extend(existing_insights)
                continue
            doc = existing_doc
        else:
            doc = TrendDocument(
                source_id=stored_source.id,
                title=result.title,
                url=result.url,
                collected_at=datetime.now(timezone.utc),
                parsed_text=result.snippet,
                content_hash=content_hash,
            )
            db.add(doc)
            db.flush()

        try:
            ai_response = await ai_client.complete(
                [AIMessage(role="user", content=_INSIGHT_PROMPT.format(
                    query=query, text=result.snippet
                ))],
                temperature=0.3,
                max_tokens=600,
            )
            raw = ai_response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed: dict = json.loads(raw)
        except Exception as exc:
            logger.warning("Insight extraction failed for %s: %s", result.url, exc)
            continue

        insight = TrendInsight(
            document_id=doc.id,
            session_id=session_id,
            summary=parsed.get("summary"),
            keywords=parsed.get("keywords", []),
            domain_tags=parsed.get("domain_tags", []),
            evidence_quote=parsed.get("evidence_quote") or result.snippet[:300],
            confidence_score=float(parsed.get("confidence_score", 0.5)),
            is_hypothesis=bool(parsed.get("is_hypothesis", False)),
        )
        db.add(insight)
        insights.append(insight)

    db.commit()
    for i in insights:
        if i.id:
            db.refresh(i)
    logger.info("[TREND] stored session=%s insights=%d results=%d query=%s",
                session_id, len(insights), len(results), search_query[:100])
    return insights


def _get_or_create_search_source(db: Session, name: str) -> TrendSource:
    source = db.query(TrendSource).filter_by(name=name).first()
    if not source:
        source = TrendSource(name=name, is_active=True)
        db.add(source)
        db.flush()
    return source
