"""Analyze reference use case.

Calls ModelPort for ReferenceAnalysis.
"""
from logging import getLogger
from typing import Any
from uuid import UUID

from apps.references.application.dtos import ReferenceAssetDTO
from apps.references.application.ports import ModelPort
from shared.domain.exceptions import OperationError

logger = getLogger(__name__)


class AnalyzeReferenceUseCase:
    """Analyze reference asset for design relevance."""

    def __init__(
        self,
        model_port: ModelPort,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            model_port: Model interface for analysis
        """
        self._model_port = model_port

    async def execute(
        self,
        asset_id: UUID,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a reference asset.

        Args:
            asset_id: ID of the asset to analyze
            context: Optional design context for analysis

        Returns:
            Analysis results with relevance score and recommendations

        Raises:
            ValueError: If asset not found
            OperationError: If analysis fails
        """
        logger.info(f"Analyzing reference asset: {asset_id}")

        try:
            # Call model port for analysis
            analysis = await self._model_port.analyze_reference(
                asset_id=str(asset_id),
                context=context,
            )

            if not analysis:
                raise OperationError("Model returned empty analysis")

            logger.info(f"Analysis complete for asset {asset_id}")
            return analysis

        except Exception as e:
            logger.error(f"Analysis failed for asset {asset_id}: {e}")
            raise OperationError(f"Analysis failed: {e}") from e
