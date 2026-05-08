"""Search trends use case.

Queries RAGPort for relevant insights.
Returns results with citations or explicit insufficient_evidence flag.
"""
from logging import getLogger
from typing import Any

from apps.trend_knowledge.application.dtos import (
    SearchTrendRequest,
    TrendSearchResponse,
)
from apps.trend_knowledge.application.ports import RAGPort
from apps.trend_knowledge.domain.entities import TrendInsight
from shared.domain.exceptions import ValidationError

logger = getLogger(__name__)


class SearchTrendsUseCase:
    """Search trend insights using RAG."""

    def __init__(
        self,
        rag_port: RAGPort,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            rag_port: RAG interface for semantic search
        """
        self._rag_port = rag_port

    async def execute(self, request: SearchTrendRequest) -> TrendSearchResponse:
        """Search for trend insights matching query.

        Args:
            request: Search request with query, filters, and pagination

        Returns:
            Search response with insights, metadata, and evidence flag

        Raises:
            ValidationError: If query is invalid
        """
        # Validate query
        if not request.query or not request.query.strip():
            raise ValidationError(
                field="query",
                message="Search query cannot be empty",
            )

        logger.info(
            f"Searching trends: query='{request.query}', "
            f"domain={request.domain}, min_confidence={request.min_confidence}"
        )

        try:
            # Query RAG port
            results = await self._rag_port.search(
                query_text=request.query,
                domain=request.domain,
                date_range=request.date_range,
                min_confidence=request.min_confidence,
                limit=request.max_results or 10,
            )

            # Check for insufficient evidence
            if not results:
                logger.info(f"No results found for query: {request.query}")
                return TrendSearchResponse(
                    insights=[],
                    total=0,
                    has_more=False,
                    insufficient_evidence=True,
                )

            # Convert to insight DTOs
            insight_dtos = []
            for insight in results:
                if isinstance(insight, TrendInsight):
                    insight_dtos.append({
                        "id": str(insight.id),
                        "summary": insight.summary,
                        "keywords": insight.keywords,
                        "evidence_quote": insight.evidence_quote,
                        "confidence": insight.confidence,
                        "document_id": str(insight.document_id),
                        "created_at": insight.created_at.isoformat(),
                    })
                else:
                    # Handle dict results from RAG port
                    insight_dtos.append({
                        "id": str(insight.get("id")),
                        "summary": insight.get("summary"),
                        "keywords": insight.get("keywords", []),
                        "evidence_quote": insight.get("evidence_quote", ""),
                        "confidence": insight.get("confidence", 0.0),
                        "document_id": str(insight.get("document_id")),
                        "created_at": insight.get("created_at"),
                    })

            return TrendSearchResponse(
                insights=insight_dtos,
                total=len(insight_dtos),
                has_more=False,  # TODO: Implement pagination
                insufficient_evidence=False,
            )

        except Exception as e:
            logger.error(f"Search failed for query '{request.query}': {e}")
            raise
