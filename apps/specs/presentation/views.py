"""Django REST views for specs module."""
from uuid import UUID

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.specs.application.use_cases import (
    ApproveSpecUseCase,
    CreateSpecDocumentUseCase,
    GetSpecDocumentUseCase,
    ListDomainPacksUseCase,
    RejectSpecUseCase,
    SubmitForReviewUseCase,
)
from apps.specs.domain.services import (
    DomainPackResolver,
    SpecDocumentValidator,
    SpecVersionManager,
)
from apps.specs.infrastructure.adapters import (
    DjangoORMAbstractionRuleAdapter,
    DjangoORMConceptAdapter,
    DjangoORMGenerationJobAdapter,
    DjangoORMSessionAdapter,
)
from apps.specs.infrastructure.repositories import (
    DjangoDomainPackRepository,
    DjangoSpecDocumentRepository,
)
from apps.specs.presentation.serializers import (
    ApproveSpecSerializer,
    CreateSpecSerializer,
    DomainPackSerializer,
    RejectSpecSerializer,
    SpecDocumentSerializer,
    SubmitForReviewSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
async def list_domain_packs(request: Request):
    """List all available domain packs.

    Args:
        request: HTTP request

    Returns:
        JSON response with list of domain packs
    """
    try:
        use_case = ListDomainPacksUseCase(DjangoDomainPackRepository())
        result = await use_case.execute()

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DomainPackSerializer(
            [DomainPackSerializer.from_dto(dto).data for dto in result.value],
            many=True,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def create_spec(request: Request):
    """Create a new spec document.

    Args:
        request: HTTP request with spec data

    Returns:
        JSON response with created spec
    """
    try:
        serializer = CreateSpecSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = CreateSpecDocumentUseCase(
            spec_repository=DjangoSpecDocumentRepository(),
            domain_pack_repository=DjangoDomainPackRepository(),
            session_port=DjangoORMSessionAdapter(),
            concept_port=DjangoORMConceptAdapter(),
            abstraction_rule_port=DjangoORMAbstractionRuleAdapter(),
            generation_job_port=DjangoORMGenerationJobAdapter(),
            domain_pack_resolver=DomainPackResolver(),
        )

        request_dto = serializer.to_request_dto()
        result = await use_case.execute(request_dto)

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = SpecDocumentSerializer.from_dto(result.value)
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
async def submit_for_review(request: Request):
    """Submit a spec document for review.

    Args:
        request: HTTP request with submission data

    Returns:
        JSON response with submitted spec
    """
    try:
        serializer = SubmitForReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = SubmitForReviewUseCase(
            spec_repository=DjangoSpecDocumentRepository(),
            validator=SpecDocumentValidator(),
        )

        request_dto = serializer.to_request_dto()
        result = await use_case.execute(request_dto)

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = SpecDocumentSerializer.from_dto(result.value)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def approve_spec(request: Request):
    """Approve a spec document.

    Args:
        request: HTTP request with approval data

    Returns:
        JSON response with approved spec
    """
    try:
        serializer = ApproveSpecSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = ApproveSpecUseCase(
            spec_repository=DjangoSpecDocumentRepository(),
            validator=SpecDocumentValidator(),
            version_manager=SpecVersionManager(),
        )

        request_dto = serializer.to_request_dto()
        result = await use_case.execute(request_dto)

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = SpecDocumentSerializer.from_dto(result.value)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def reject_spec(request: Request):
    """Reject a spec document.

    Args:
        request: HTTP request with rejection data

    Returns:
        JSON response with rejected spec
    """
    try:
        serializer = RejectSpecSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = RejectSpecUseCase(spec_repository=DjangoSpecDocumentRepository())

        request_dto = serializer.to_request_dto()
        result = await use_case.execute(request_dto)

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = SpecDocumentSerializer.from_dto(result.value)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
async def get_spec(request: Request, spec_id: str):
    """Get a spec document by ID.

    Args:
        request: HTTP request
        spec_id: Spec UUID as string

    Returns:
        JSON response with spec document
    """
    try:
        use_case = GetSpecDocumentUseCase(DjangoSpecDocumentRepository())
        result = await use_case.execute(UUID(spec_id))

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SpecDocumentSerializer.from_dto(result.value)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
