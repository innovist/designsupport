"""Text helpers for trend insights consumed by downstream pipeline stages."""

from __future__ import annotations

from app.models.trends import TrendInsight


def format_insight_for_prompt(insight: TrendInsight) -> str | None:
    """Return a grounded one-line evidence entry for AI prompts."""
    text = _insight_text(insight)
    if not text:
        return None

    sources = insight_source_urls(insight)
    if sources:
        return f"- {text} (sources: {', '.join(sources)})"
    return f"- {text}"


def format_insight_summary_line(insight: TrendInsight, index: int) -> str:
    """Return a human-readable trend summary without assuming evidence_quote."""
    text = _insight_text(insight)
    if text:
        return f"{index}. {text[:160]}"

    sources = insight_source_urls(insight)
    if sources:
        return f"{index}. 출처 기반 트렌드 근거: {sources[0]}"
    return f"{index}. 요약 정보가 비어 있는 트렌드 근거"


def insight_source_urls(insight: TrendInsight) -> list[str]:
    urls: list[str] = []
    for item in insight.source_urls or []:
        if isinstance(item, dict):
            url = item.get("url")
        else:
            url = item
        if isinstance(url, str) and url and url not in urls:
            urls.append(url)

    document = getattr(insight, "document", None)
    document_url = getattr(document, "url", None)
    if document_url and document_url not in urls:
        urls.append(document_url)
    return urls


def _insight_text(insight: TrendInsight) -> str | None:
    for value in (insight.summary, insight.evidence_quote, insight.title):
        if isinstance(value, str) and value.strip():
            return value.strip()

    keywords = insight.keywords or []
    if keywords:
        return ", ".join(str(keyword) for keyword in keywords if keyword)
    return None
