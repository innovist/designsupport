"""Tests for nullable trend-insight text handling."""

from types import SimpleNamespace

from app.application.services.pipeline_orchestrator import DesignPipelineOrchestrator
from app.application.use_cases.trends.insight_text import (
    format_insight_for_prompt,
    format_insight_summary_line,
    insight_source_urls,
)


def test_prompt_evidence_uses_summary_and_source_urls_without_quote():
    insight = SimpleNamespace(
        title="순환 소재",
        summary="재활용 소재와 모듈형 구조가 함께 강조된다.",
        evidence_quote=None,
        keywords=["재활용", "모듈"],
        source_urls=[{"url": "https://example.com/a", "title": "A"}],
        document=SimpleNamespace(url="https://example.com/root"),
    )

    line = format_insight_for_prompt(insight)

    assert "재활용 소재" in line
    assert "https://example.com/a" in line
    assert "https://example.com/root" in line


def test_summary_line_does_not_slice_nullable_evidence_quote():
    insight = SimpleNamespace(
        title="가벼운 구조",
        summary=None,
        evidence_quote=None,
        keywords=[],
        source_urls=[{"url": "https://example.com/source"}],
        document=None,
    )

    assert format_insight_summary_line(insight, 1) == "1. 가벼운 구조"


def test_pipeline_trend_summary_accepts_synthesized_insight_without_quote():
    insight = SimpleNamespace(
        title="매트한 금속감",
        summary=None,
        evidence_quote=None,
        keywords=[],
        source_urls=[{"url": "https://example.com/material"}],
        document=None,
    )

    summary = DesignPipelineOrchestrator._format_trend_summary([insight])

    assert "매트한 금속감" in summary


def test_source_urls_deduplicates_structured_and_document_sources():
    insight = SimpleNamespace(
        source_urls=[
            {"url": "https://example.com/a"},
            "https://example.com/a",
            {"title": "missing url"},
        ],
        document=SimpleNamespace(url="https://example.com/b"),
    )

    assert insight_source_urls(insight) == [
        "https://example.com/a",
        "https://example.com/b",
    ]
