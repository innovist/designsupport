"""Django REST views for concepts module."""
from uuid import UUID

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from apps.concepts.application.use_cases.decide_concept import DecideConceptUseCase
from apps.concepts.application.use_cases.list_concepts import ListConceptsBySessionUseCase
from apps.concepts.application.use_cases.propose_concept import ProposeConceptUseCase
from apps.concepts.domain.services import ConceptScorer
from apps.concepts.infrastructure.adapters.reference_analysis_adapter import ReferenceAnalysisAdapter
from apps.concepts.infrastructure.adapters.session_adapter import DesignSessionAdapter
from apps.concepts.infrastructure.adapters.trend_insight_adapter import TrendInsightAdapter
from apps.concepts.infrastructure.repositories.concept_repository import (
    DjangoConceptRepository,
    DjangoDecisionRepository,
)
from apps.concepts.presentation.serializers import (
    ConceptCandidateSerializer,
    ConceptDecisionSerializer,
    DecideConceptSerializer,
    ProposeConceptSerializer,
)


# @MX:ANCHOR: [AUTO] Concept listing endpoint for session-based retrieval
# @MX:REASON: Primary API for fetching concept candidates with scoring data
@api_view(["GET"])
@permission_classes([IsAuthenticated])
async def list_concepts(request: Request, session_id: str):
    """List all concepts for a session.

    Args:
        request: HTTP request
        session_id: Session UUID as string

    Returns:
        JSON response with list of concepts
    """
    try:
        use_case = ListConceptsBySessionUseCase(DjangoConceptRepository())
        result = await use_case.execute(UUID(session_id))

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ConceptCandidateSerializer(
            result.value, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def propose_concept(request: Request):
    """Propose a new concept candidate.

    Args:
        request: HTTP request with concept data

    Returns:
        JSON response with created concept
    """
    try:
        serializer = ProposeConceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = ProposeConceptUseCase(
            concept_repository=DjangoConceptRepository(),
            decision_repository=DjangoDecisionRepository(),
            session_port=DesignSessionAdapter(),
            trend_insight_port=TrendInsightAdapter(),
            reference_analysis_port=ReferenceAnalysisAdapter(),
            scorer=ConceptScorer(),
        )

        request_dto = serializer.to_request_dto()
        result = await use_case.execute(request_dto)

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = ConceptCandidateSerializer.from_dto(result.value)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def decide_concept(request: Request):
    """Record a decision on a concept.

    Args:
        request: HTTP request with decision data

    Returns:
        JSON response with recorded decision
    """
    try:
        serializer = DecideConceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = DecideConceptUseCase(
            concept_repository=DjangoConceptRepository(),
            decision_repository=DjangoDecisionRepository(),
        )

        request_dto = serializer.to_request_dto()
        result = await use_case.execute(request_dto)

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = ConceptDecisionSerializer.from_dto(result.value)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
