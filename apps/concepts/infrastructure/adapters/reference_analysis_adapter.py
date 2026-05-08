"""Adapter for references module port.

Implements ReferenceAnalysisPort from concepts.application.ports.
"""
from uuid import UUID

from apps.concepts.application.ports import ReferenceAnalysisPort


class ReferenceAnalysisAdapter(ReferenceAnalysisPort):
    """Adapter for accessing reference analyses.

    This adapter connects to the references module to validate
    reference analysis references.
    """

    async def analyses_exist(self, analysis_ids: list[UUID]) -> bool:
        """Check if reference analyses exist.

        Args:
            analysis_ids: List of analysis UUIDs

        Returns:
            True if all analyses exist, False otherwise
        """
        if not analysis_ids:
            return True

        try:
            # Import here to avoid circular dependencies
            from apps.references.application.use_cases.get_reference_analysis import GetReferenceAnalysisUseCase
            from apps.references.infrastructure.repositories.analysis_repository import DjangoAnalysisRepository

            use_case = GetReferenceAnalysisUseCase(DjangoAnalysisRepository())

            # Check each analysis
            for analysis_id in analysis_ids:
                result = await use_case.execute(analysis_id)
                if result.is_failure or result.value is None:
                    return False

            return True

        except ImportError:
            # references module not available
            return False
        except Exception:
            return False
