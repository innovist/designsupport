"""DRF views for References.

REST Framework views for reference search and analysis.
"""
from logging import getLogger
from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.references.application.dtos import SearchReferenceRequest
from apps.references.application.use_cases.analyze_reference import (
    AnalyzeReferenceUseCase,
)
from apps.references.application.use_cases.search_references import (
    SearchReferencesUseCase,
)
from apps.references.presentation.serializers import (
    ReferenceAnalysisSerializer,
    ReferenceSearchResponseSerializer,
    SearchReferenceRequestSerializer,
)

logger = getLogger(__name__)


class ReferenceSearchView(ViewSet):
    """Main search endpoint for reference assets."""

    def __init__(self, **kwargs: Any):
        """Initialize viewset with use cases."""
        super().__init__(**kwargs)
        self._search_use_case: SearchReferencesUseCase | None = None

    def create(self, request: Request) -> Response:
        """Search for reference assets across providers.

        POST /api/references/search/
        {
            "query_kind": "keyword",
            "payload": {"query": "minimalist fashion"},
            "domain": "fashion",
            "max_results": 20
        }
        """
        serializer = SearchReferenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            # Convert to request DTO
            search_request = SearchReferenceRequest(
                query_kind=data["query_kind"],
                payload=data["payload"],
                session_id=data.get("session_id"),
                domain=data.get("domain"),
                max_results=data.get("max_results"),
            )

            # Call use case (placeholder)
            # response = await self._search_use_case.execute(search_request)

            return Response({
                "detail": "Reference search not yet implemented",
                "query_kind": data["query_kind"],
            }, status=status.HTTP_501_NOT_IMPLEMENTED)

        except Exception as e:
            logger.error(f"Reference search failed: {e}")
            return Response({
                "detail": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReferenceAnalysisView(ViewSet):
    """Analysis endpoint for reference assets."""

    def __init__(self, **kwargs: Any):
        """Initialize viewset with use cases."""
        super().__init__(**kwargs)
        self._analyze_use_case: AnalyzeReferenceUseCase | None = None

    def create(self, request: Request, asset_id: str | None = None) -> Response:
        """Analyze a reference asset for design relevance.

        POST /api/references/analyze/{asset_id}/
        {
            "context": "sustainable fashion design"
        }
        """
        context = request.data.get("context")

        try:
            # Call use case (placeholder)
            # analysis = await self._analyze_use_case.execute(asset_id, context)

            return Response({
                "detail": "Reference analysis not yet implemented",
                "asset_id": asset_id,
            }, status=status.HTTP_501_NOT_IMPLEMENTED)

        except Exception as e:
            logger.error(f"Reference analysis failed: {e}")
            return Response({
                "detail": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
