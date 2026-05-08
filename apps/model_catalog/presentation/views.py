"""DRF views for model catalog API."""
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.model_catalog.application.use_cases import (
    GetModelMetricsUseCase,
    InvokeModelUseCase,
    ListModelsUseCase,
    ListProvidersUseCase,
    RegisterModelUseCase,
    RegisterProviderUseCase,
    RollbackPolicyUseCase,
    UpdateFeaturePolicyUseCase,
)
from apps.model_catalog.domain.services import CostGuard, ModelRouter, PolicyVersionManager
from apps.model_catalog.infrastructure.repositories import (
    FeatureModelPolicyRepository,
    ModelCatalogRepository,
    ModelInvocationRepository,
    ModelProviderRepository,
    PolicyChangeLogRepository,
)
from apps.model_catalog.presentation.serializers import (
    FeatureModelPolicySerializer,
    InvokeModelRequestSerializer,
    InvokeModelResponseSerializer,
    ModelCatalogSerializer,
    ModelInvocationSerializer,
    ModelProviderSerializer,
    PolicyChangeLogSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_providers(request):
    """List all model providers.

    GET /api/model-catalog/providers/
    """
    use_case = ListProvidersUseCase(
        provider_repository=ModelProviderRepository(),
    )

    active_only = request.query_params.get("active_only", "true").lower() == "true"
    result = use_case.execute(active_only=active_only)

    if result.is_failure:
        return Response(
            {"error": result.error.message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ModelProviderSerializer(result.value, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_provider(request):
    """Register a new model provider.

    POST /api/model-catalog/providers/register/
    """
    serializer = ModelProviderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    use_case = RegisterProviderUseCase(
        provider_repository=ModelProviderRepository(),
    )

    result = use_case.execute(**serializer.validated_data)

    if result.is_failure:
        return Response(
            {"error": result.error.message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    response_serializer = ModelProviderSerializer(result.value)
    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_models(request):
    """List models with optional filters.

    GET /api/model-catalog/models/?provider_id=X&type=Y&active_only=true
    """
    use_case = ListModelsUseCase(
        model_repository=ModelCatalogRepository(),
    )

    provider_id = request.query_params.get("provider_id")
    model_type = request.query_params.get("type")
    active_only = request.query_params.get("active_only", "true").lower() == "true"

    result = use_case.execute(
        provider_id=provider_id,
        model_type=model_type,
        active_only=active_only,
    )

    if result.is_failure:
        return Response(
            {"error": result.error.message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ModelCatalogSerializer(result.value, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_model(request):
    """Register a new model in catalog.

    POST /api/model-catalog/models/register/
    """
    serializer = ModelCatalogSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Validation failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    use_case = RegisterModelUseCase(
        model_repository=ModelCatalogRepository(),
        provider_repository=ModelProviderRepository(),
    )

    result = use_case.execute(**serializer.validated_data)

    if result.is_failure:
        return Response(
            {"error": result.error.message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    response_serializer = ModelCatalogSerializer(result.value)
    return Response(
        response_serializer.data,
        status=status.HTTP_201_CREATED,
    )


# @MX:ANCHOR: Main API endpoint for model invocation across all features
# @MX:REASON: Central entry point for AI model calls; routes through ModelRouter
class InvokeModelView(APIView):
    """View for invoking models through the router.

    POST /api/model-catalog/invocations/
    """

    permission_classes = [IsAuthenticated]

    # @MX:WARN: ModelRouter invoke() call with external API fallback chain
    # @MX:REASON: Multiple HTTP requests can fail; requires proper error handling
    def post(self, request):
        """Invoke a model for a feature."""
        serializer = InvokeModelRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get tenant and workspace from request
        tenant_id = getattr(request, "tenant_id", "default")
        workspace_id = getattr(request, "workspace_id", "default")

        # Initialize router with repositories
        cost_guard = CostGuard(
            policy_repository=FeatureModelPolicyRepository(),
        )
        # Wire model repository for cost estimation
        cost_guard.policy_repository.model_repository = ModelCatalogRepository()

        router = ModelRouter(
            policy_repository=FeatureModelPolicyRepository(),
            model_repository=ModelCatalogRepository(),
            invocation_repository=ModelInvocationRepository(),
            cost_guard=cost_guard,
        )

        use_case = InvokeModelUseCase(model_router=router)

        result = use_case.execute(
            feature_key=serializer.validated_data["feature_key"],
            payload=serializer.validated_data["payload"],
            options=serializer.validated_data.get("options", {}),
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            session_id=serializer.validated_data.get("session_id"),
        )

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = InvokeModelResponseSerializer(result.value)
        return Response(response_serializer.data)


class FeaturePolicyView(APIView):
    """View for managing feature model policies.

    GET /api/model-catalog/policies/features/
    POST /api/model-catalog/policies/features/
    PUT /api/model-catalog/policies/features/{id}/
    POST /api/model-catalog/policies/features/{id}/rollback/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all feature policies."""
        repository = FeatureModelPolicyRepository()
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        policies = repository.list_all(active_only=active_only)
        serializer = FeatureModelPolicySerializer(policies, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new feature policy."""
        serializer = FeatureModelPolicySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create via repository
        policy = serializer.save()
        repository = FeatureModelPolicyRepository()
        created = repository.create(policy)

        response_serializer = FeatureModelPolicySerializer(created)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def put(self, request, id):
        """Update a feature policy (creates new version)."""
        serializer = FeatureModelPolicySerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = UpdateFeaturePolicyUseCase(
            policy_repository=FeatureModelPolicyRepository(),
            change_log_repository=PolicyChangeLogRepository(),
            version_manager=PolicyVersionManager(
                policy_repository=FeatureModelPolicyRepository(),
                change_log_repository=PolicyChangeLogRepository(),
            ),
        )

        result = use_case.execute(
            policy_id=id,
            actor_id=request.user.id,
            reason=request.data.get("reason", "Policy update via API"),
            **serializer.validated_data,
        )

        if result.is_failure:
            return Response(
                {"error": result.error.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = FeatureModelPolicySerializer(result.value)
        return Response(response_serializer.data)

    def post(self, request, id, action="rollback"):
        """Handle policy actions (rollback, etc.)."""
        if action == "rollback":
            target_version = request.data.get("version")
            if not target_version:
                return Response(
                    {"error": "version parameter required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            use_case = RollbackPolicyUseCase(
                policy_repository=FeatureModelPolicyRepository(),
                change_log_repository=PolicyChangeLogRepository(),
                version_manager=PolicyVersionManager(
                    policy_repository=FeatureModelPolicyRepository(),
                    change_log_repository=PolicyChangeLogRepository(),
                ),
            )

            result = use_case.execute(
                policy_type="feature",
                policy_id=id,
                target_version=target_version,
                actor_id=request.user.id,
                reason=request.data.get("reason", "Rollback via API"),
            )

            if result.is_failure:
                return Response(
                    {"error": result.error.message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            response_serializer = FeatureModelPolicySerializer(result.value)
            return Response(response_serializer.data)

        return Response(
            {"error": f"Unknown action: {action}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_model_metrics(request):
    """Get aggregated metrics for a feature.

    GET /api/model-catalog/metrics/?feature_key=X&start_date=Y&end_date=Z
    """
    feature_key = request.query_params.get("feature_key")
    if not feature_key:
        return Response(
            {"error": "feature_key parameter required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    start_date_str = request.query_params.get("start_date")
    end_date_str = request.query_params.get("end_date")

    start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
    end_date = datetime.fromisoformat(end_date_str) if end_date_str else None

    use_case = GetModelMetricsUseCase(
        invocation_repository=ModelInvocationRepository(),
    )

    result = use_case.execute(
        feature_key=feature_key,
        start_time=start_date,
        end_time=end_date,
    )

    if result.is_failure:
        return Response(
            {"error": result.error.message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(result.value)
