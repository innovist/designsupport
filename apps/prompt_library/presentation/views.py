"""API views for prompt library module."""
from uuid import UUID

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from shared.domain.exceptions import ValidationError

from apps.prompt_library.application.use_cases.search_patterns import SearchPatternsUseCase
from apps.prompt_library.application.use_cases.validate_prompt import ValidatePromptUseCase
from apps.prompt_library.application.use_cases.log_violation import LogViolationUseCase
from apps.prompt_library.infrastructure.repositories import (
    DjangoPromptPatternRepository,
    DjangoPromptSafetyViolationRepository,
)
from apps.prompt_library.presentation.serializers import (
    PromptPatternSerializer,
    PromptSafetyViolationSerializer,
    SearchPatternsRequestSerializer,
    ValidatePromptRequestSerializer,
    ValidatePromptResponseSerializer,
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_patterns(request: Request) -> Response:
    """List all active prompt patterns.

    GET /api/prompt-library/patterns/
    """
    try:
        # Initialize use case
        pattern_repo = DjangoPromptPatternRepository()
        use_case = SearchPatternsUseCase(pattern_repository=pattern_repo)

        # Execute use case (no filters = all active)
        result = async_to_sync(use_case.execute)()

        if result.is_failure:
            return Response(
                {'error': str(result.error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        patterns = result.value

        # Serialize response
        serializer = PromptPatternSerializer(patterns, many=True)
        return Response({
            'patterns': serializer.data,
            'count': len(patterns),
        })

    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_patterns(request: Request) -> Response:
    """Search prompt patterns by category and/or domain tags.

    GET /api/prompt-library/patterns/search/?category=line_to_render&domain_tags[]=industrial
    """
    try:
        # Validate request
        request_serializer = SearchPatternsRequestSerializer(data=request.query_params)
        if not request_serializer.is_valid():
            return Response(
                {'errors': request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request_serializer.validated_data

        # Initialize use case
        pattern_repo = DjangoPromptPatternRepository()
        use_case = SearchPatternsUseCase(pattern_repository=pattern_repo)

        # Execute use case
        result = async_to_sync(use_case.execute)(
            category=data.get('category'),
            domain_tags=data.get('domain_tags'),
        )

        if result.is_failure:
            return Response(
                {'error': str(result.error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        patterns = result.value

        # Serialize response
        serializer = PromptPatternSerializer(patterns, many=True)
        return Response({
            'patterns': serializer.data,
            'count': len(patterns),
        })

    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_prompt(request: Request) -> Response:
    """Validate a prompt against safety rules.

    POST /api/prompt-library/prompts/validate/
    {
        "session_id": "uuid",
        "prompt_id": "uuid" (optional),
        "prompt_text": "text to validate",
        "source_refs": ["uuid", ...]
    }
    """
    try:
        # Validate request
        request_serializer = ValidatePromptRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {'errors': request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request_serializer.validated_data

        # Initialize use case
        pattern_repo = DjangoPromptPatternRepository()
        violation_repo = DjangoPromptSafetyViolationRepository()
        use_case = ValidatePromptUseCase(
            pattern_repository=pattern_repo,
            violation_repository=violation_repo,
        )

        # Execute use case
        result = async_to_sync(use_case.execute)(
            session_id=data['session_id'],
            prompt_id=data.get('prompt_id'),
            prompt_text=data['prompt_text'],
            source_refs=data.get('source_refs', []),
        )

        if result.is_failure:
            return Response(
                {'error': str(result.error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = result.value

        # Serialize response
        response_serializer = ValidatePromptResponseSerializer(response_data)
        return Response(response_serializer.data)

    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_violation(request: Request) -> Response:
    """Log a prompt safety violation.

    POST /api/prompt-library/violations/
    {
        "session_id": "uuid",
        "prompt_id": "uuid" (optional),
        "reason": "violation reason",
        "source_refs": ["uuid", ...]
    }
    """
    try:
        from uuid import UUID

        # Extract data
        session_id = UUID(request.data.get('session_id'))
        prompt_id = request.data.get('prompt_id')
        if prompt_id:
            prompt_id = UUID(prompt_id)
        reason = request.data.get('reason')
        source_refs = request.data.get('source_refs', [])
        source_refs = [UUID(ref) for ref in source_refs]

        # Initialize use case
        violation_repo = DjangoPromptSafetyViolationRepository()
        use_case = LogViolationUseCase(violation_repository=violation_repo)

        # Execute use case
        result = async_to_sync(use_case.execute)(
            session_id=session_id,
            prompt_id=prompt_id,
            reason=reason,
            source_refs=source_refs,
        )

        if result.is_failure:
            return Response(
                {'error': str(result.error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        violation = result.value

        # Serialize response
        serializer = PromptSafetyViolationSerializer(violation)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    except (ValueError, ValidationError) as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
