"""DRF views for generation module."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from uuid import UUID

from apps.generation.application.use_cases.create_generation_job import CreateGenerationJobUseCase
from apps.generation.application.use_cases.execute_generation_job import ExecuteGenerationJobUseCase
from apps.generation.application.use_cases.list_generation_jobs import ListGenerationJobsUseCase
from apps.generation.application.use_cases.get_generation_result import GetGenerationResultUseCase
from apps.generation.application.dtos import ExecuteJobRequest
from apps.generation.domain.services import GenerationJobValidator
from apps.generation.infrastructure.repositories.generation_job_repository import DjangoGenerationJobRepository
from apps.generation.infrastructure.repositories.generated_design_repository import DjangoGeneratedDesignRepository
from apps.generation.presentation.serializers import (
    CreateGenerationJobSerializer,
    GenerationJobSerializer,
    GeneratedDesignSerializer,
    ExecuteJobSerializer,
    ExecuteJobResponseSerializer
)
from shared.domain.exceptions import NotFoundError, ValidationError


# @MX:ANCHOR: [AUTO] Generation API endpoints with job lifecycle management
# @MX:REASON: Primary REST interface for job creation, execution, and result retrieval
# @MX:SPEC: REQ-03-GEN-001, REQ-03-GEN-002
class GenerationJobViewSet(viewsets.ViewSet):
    """ViewSet for GenerationJob operations."""

    def __init__(self, *args, **kwargs):
        """Initialize viewset with use cases."""
        super().__init__(*args, **kwargs)

        # Initialize repositories
        job_repo = DjangoGenerationJobRepository()
        design_repo = DjangoGeneratedDesignRepository()
        validator = GenerationJobValidator()

        # Initialize use cases
        self.create_use_case = CreateGenerationJobUseCase(job_repo, validator)
        self.list_use_case = ListGenerationJobsUseCase(job_repo)
        self.get_result_use_case = GetGenerationResultUseCase(job_repo, design_repo)

    @swagger_auto_schema(
        operation_description="Create a new generation job",
        request_body=CreateGenerationJobSerializer,
        responses={201: GenerationJobSerializer}
    )
    # @MX:WARN: [AUTO] Async execution in sync context with asyncio.run
    # @MX:REASON: Blocking call in view may affect request handling; consider proper async view
    def create(self, request):
        """Create a new generation job.

        REQ-03-GEN-001: GenerationJob tracks all creation metadata
        REQ-03-GEN-002: Job MUST link to at least one of: brief, concept, rule, reference
        """
        serializer = CreateGenerationJobSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        dto = serializer.to_request()

        # Execute use case
        import asyncio
        result = asyncio.run(self.create_use_case.execute(dto))

        if result.is_failure:
            error = result.error
            return Response(
                {"error": error.message, "details": error.details},
                status=status.HTTP_400_BAD_REQUEST if isinstance(error, ValidationError) else status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = result.value
        serialized = GenerationJobSerializer.from_response(response)

        return Response(serialized, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="List generation jobs for a session",
        manual_parameters=[
            openapi.Parameter(
                "session_id",
                openapi.IN_QUERY,
                description="Session ID",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Filter by status",
                type=openapi.TYPE_STRING,
                required=False,
                enum=["queued", "running", "completed", "failed", "cancelled"]
            ),
            openapi.Parameter(
                "kind",
                openapi.IN_QUERY,
                description="Filter by kind",
                type=openapi.TYPE_STRING,
                required=False,
                enum=["sketch", "refinement", "variation", "domain_application"]
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Maximum results",
                type=openapi.TYPE_INTEGER,
                required=False,
                default=50
            )
        ],
        responses={200: GenerationJobSerializer(many=True)}
    )
    def list(self, request):
        """List generation jobs for a session."""
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.generation.domain.value_objects import GenerationStatus, GenerationKind

        # Parse optional filters
        status_filter = None
        kind_filter = None

        status_param = request.query_params.get("status")
        if status_param:
            try:
                status_filter = GenerationStatus(status_param)
            except ValueError:
                return Response(
                    {"error": f"Invalid status: {status_param}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        kind_param = request.query_params.get("kind")
        if kind_param:
            try:
                kind_filter = GenerationKind(kind_param)
            except ValueError:
                return Response(
                    {"error": f"Invalid kind: {kind_param}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        limit = int(request.query_params.get("limit", 50))

        # Execute use case
        import asyncio
        result = asyncio.run(self.list_use_case.execute(
            session_id=session_id,
            status=status_filter,
            kind=kind_filter,
            limit=limit
        ))

        if result.is_failure:
            return Response(
                {"error": str(result.error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        jobs = result.value
        serialized = [GenerationJobSerializer.from_response(job) for job in jobs]

        return Response(serialized)

    @swagger_auto_schema(
        operation_description="Get generation result details",
        manual_parameters=[
            openapi.Parameter(
                "job_id",
                openapi.IN_PATH,
                description="Job ID",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: GenerationJobSerializer}
    )
    def retrieve(self, request, job_id=None):
        """Get generation result details."""
        if not job_id:
            return Response(
                {"error": "job_id path parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Execute use case
        import asyncio
        result = asyncio.run(self.get_result_use_case.execute(job_id))

        if result.is_failure:
            error = result.error
            if isinstance(error, NotFoundError):
                return Response(
                    {"error": error.message},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        data = result.value

        return Response({
            "job": GenerationJobSerializer.from_response(data["job"]),
            "designs": [GeneratedDesignSerializer.from_response(d) for d in data["designs"]]
        })

    @swagger_auto_schema(
        operation_description="Execute a generation job",
        manual_parameters=[
            openapi.Parameter(
                "job_id",
                openapi.IN_PATH,
                description="Job ID",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ExecuteJobSerializer,
        responses={202: ExecuteJobResponseSerializer}
    )
    @action(detail=True, methods=["post"])
    def execute(self, request, job_id=None):
        """Execute a generation job.

        This endpoint triggers async execution via Celery.
        """
        if not job_id:
            return Response(
                {"error": "job_id path parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ExecuteJobSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        dto = serializer.to_request()

        # Trigger async task
        from apps.generation.infrastructure.tasks import execute_generation_task

        task = execute_generation_task.delay(str(dto.job_id))

        return Response({
            "task_id": task.id,
            "job_id": str(dto.job_id),
            "status": "queued_for_execution"
        }, status=status.HTTP_202_ACCEPTED)


class GenerationJobStatusView(APIView):
    """View for checking job execution status."""

    @swagger_auto_schema(
        operation_description="Check job execution status",
        manual_parameters=[
            openapi.Parameter(
                "task_id",
                openapi.IN_QUERY,
                description="Celery task ID",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "task_id": openapi.Schema(type=openapi.TYPE_STRING),
                "status": openapi.Schema(type=openapi.TYPE_STRING),
                "result": openapi.Schema(type=openapi.TYPE_OBJECT)
            }
        )}
    )
    def get(self, request):
        """Check the status of an async generation task."""
        from celery.result import AsyncResult

        task_id = request.query_params.get("task_id")

        if not task_id:
            return Response(
                {"error": "task_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = AsyncResult(task_id)

        response_data = {
            "task_id": task_id,
            "status": task.state,
            "result": task.result if task.ready() else None
        }

        if task.failed():
            response_data["error"] = str(task.info)

        return Response(response_data)
