"""Adapter for trend_knowledge module port.

Implements TrendInsightPort from concepts.application.ports.
"""
from uuid import UUID

from apps.concepts.application.ports import TrendInsightPort


class TrendInsightAdapter(TrendInsightPort):
    """Adapter for accessing trend insights.

    This adapter connects to the trend_knowledge module to validate
    trend insight references.
    """

    async def insights_exist(self, insight_ids: list[UUID]) -> bool:
        """Check if trend insights exist.

        Args:
            insight_ids: List of insight UUIDs

        Returns:
            True if all insights exist, False otherwise
        """
        if not insight_ids:
            return True

        try:
            # Import here to avoid circular dependencies
            from apps.trend_knowledge.application.use_cases.list_insights import ListInsightsUseCase
            from apps.trend_knowledge.infrastructure.repositories.insight_repository import DjangoInsightRepository

            use_case = ListInsightsUseCase(DjangoInsightRepository())

            # Check each insight
            for insight_id in insight_ids:
                result = await use_case.execute(insight_id)
                if result.is_failure or result.value is None:
                    return False

            return True

        except ImportError:
            # trend_knowledge module not available
            return False
        except Exception:
            return False
