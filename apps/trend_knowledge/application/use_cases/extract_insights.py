"""Extract insights use case.

Calls ModelPort to extract TrendInsight with evidence_quote.
Calculates confidence via InsightConfidenceCalculator.
"""
from datetime import datetime, timezone
from logging import getLogger
from typing import Any
from uuid import UUID, uuid4

from apps.trend_knowledge.application.ports import (
    ModelPort,
    TrendDocumentRepositoryPort,
    TrendInsightRepositoryPort,
)
from apps.trend_knowledge.domain.entities import TrendInsight
from apps.trend_knowledge.domain.services import InsightConfidenceCalculator
from shared.domain.exceptions import OperationError

logger = getLogger(__name__)


class ExtractInsightsUseCase:
    """Extract insights from parsed documents using model."""

    def __init__(
        self,
        document_repository: TrendDocumentRepositoryPort,
        insight_repository: TrendInsightRepositoryPort,
        model_port: ModelPort,
        confidence_calculator: InsightConfidenceCalculator,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            document_repository: Repository for document lookup
            insight_repository: Repository for insight persistence
            model_port: Model interface for insight extraction
            confidence_calculator: Service for confidence scoring
        """
        self._document_repository = document_repository
        self._insight_repository = insight_repository
        self._model_port = model_port
        self._confidence_calculator = confidence_calculator

    async def execute(self, document_id: UUID) -> list[dict[str, Any]]:
        """Extract insights from a parsed document.

        Args:
            document_id: ID of the document to analyze

        Returns:
            List of created insight metadata

        Raises:
            ValueError: If document not found or not parsed
            OperationError: If extraction fails
        """
        # Load document
        document = await self._document_repository.get_by_id(document_id)
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        if not document.parsed_text:
            raise ValueError(f"Document not parsed: {document_id}")

        logger.info(f"Extracting insights from document: {document_id}")

        try:
            # Extract insights via model
            insights_data = await self._model_port.extract_insights(
                document_text=document.parsed_text,
                domain=document.source.domain if document.source else "general",
            )

            if not insights_data:
                logger.info(f"No insights extracted from document {document_id}")
                return []

            # Create insight entities
            created_insights = []
            for insight_data in insights_data:
                # Calculate confidence score
                confidence = self._confidence_calculator.calculate(
                    summary=insight_data.get("summary", ""),
                    evidence_quote=insight_data.get("evidence_quote", ""),
                    keywords=insight_data.get("keywords", []),
                )

                insight = TrendInsight(
                    id=uuid4(),
                    document_id=document.id,
                    summary=insight_data["summary"],
                    keywords=insight_data.get("keywords", []),
                    evidence_quote=insight_data.get("evidence_quote", ""),
                    confidence=confidence,
                    created_at=datetime.now(timezone.utc),
                )

                saved_insight = await self._insight_repository.save(insight)
                created_insights.append({
                    "id": str(saved_insight.id),
                    "summary": saved_insight.summary,
                    "confidence": saved_insight.confidence,
                    "keywords": saved_insight.keywords,
                })

            logger.info(f"Extracted {len(created_insights)} insights from document {document_id}")
            return created_insights

        except Exception as e:
            logger.error(f"Insight extraction failed for document {document_id}: {e}")
            raise OperationError(f"Insight extraction failed: {e}") from e
