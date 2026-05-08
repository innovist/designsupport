"""Use cases for model catalog application layer.

Orchestrates domain logic via domain services and repositories.
"""
from datetime import datetime
from typing import Any

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.model_catalog.application.ports import (
    FeatureModelPolicyRepositoryPort,
    ModelCatalogRepositoryPort,
    ModelInvocationRepositoryPort,
    ModelProviderRepositoryPort,
    PolicyChangeLogRepositoryPort,
    PromptPolicyRepositoryPort,
)
from apps.model_catalog.domain.entities import (
    FeatureModelPolicy,
    ModelCatalog,
    ModelInvocation,
    ModelProvider,
    ModelType,
    PromptPolicy,
)
from apps.model_catalog.domain.services import ModelRouter, PolicyVersionManager


# @MX:ANCHOR: Primary use case for model invocation across all AI features
# @MX:REASON: Orchestrates ModelRouter; called by API views and background tasks
class InvokeModelUseCase:
    """Use case for invoking models through the router.

    Implements REQ-04-ROUTER-001: Single entry point for model calls.
    """

    def __init__(
        self,
        model_router: ModelRouter,
    ):
        """Initialize use case with router.

        Args:
            model_router: Configured ModelRouter instance
        """
        self.router = model_router

    async def execute(
        self,
        feature_key: str,
        payload: dict[str, Any],
        options: dict[str, Any],
        tenant_id: str,
        workspace_id: str,
        session_id: str | None = None,
    ) -> Result[dict[str, Any]]:
        """Execute model invocation.

        Args:
            feature_key: Feature identifier
            payload: Request payload
            options: Model options
            tenant_id: Tenant ID
            workspace_id: Workspace ID
            session_id: Optional session ID

        Returns:
            Result with model response or error
        """
        try:
            response, invocation = await self.router.invoke(
                feature_key=feature_key,
                payload=payload,
                options=options,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                session_id=session_id,
            )

            # Return response with invocation metadata
            return Result.success({
                "response": response,
                "invocation_id": invocation.id,
                "model_id": invocation.model_id,
                "tokens_in": invocation.tokens_in,
                "tokens_out": invocation.tokens_out,
                "cost_estimate": invocation.cost_estimate,
                "latency_ms": invocation.latency_ms,
            })

        except (NotFoundError, ValidationError) as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("invoke", f"Model invocation failed: {str(e)}")
            )


class RegisterProviderUseCase:
    """Use case for registering a new provider."""

    def __init__(
        self,
        provider_repository: ModelProviderRepositoryPort,
    ):
        """Initialize use case with repository.

        Args:
            provider_repository: Provider repository
        """
        self.provider_repository = provider_repository

    async def execute(
        self,
        name: str,
        api_key_env: str,
        base_url: str | None = None,
        endpoint_path: str | None = None,
        auth_scheme: str = "Bearer",
    ) -> Result[ModelProvider]:
        """Execute provider registration.

        Args:
            name: Provider name
            api_key_env: Environment variable for API key
            base_url: Base URL for API
            endpoint_path: Default endpoint path
            auth_scheme: Authentication scheme

        Returns:
            Result with created provider or error
        """
        try:
            # Create provider entity
            import uuid

            provider = ModelProvider(
                id=f"prov-{uuid.uuid4().hex}",
                name=name,
                api_key_env=api_key_env,
                base_url=base_url,
                endpoint_path=endpoint_path,
                auth_scheme=auth_scheme,  # type: ignore
                active=True,
            )

            # Save via repository
            created = await self.provider_repository.create(provider)

            return Result.success(created)

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("register_provider", f"Registration failed: {str(e)}")
            )


class RegisterModelUseCase:
    """Use case for registering a new model in catalog."""

    def __init__(
        self,
        model_repository: ModelCatalogRepositoryPort,
        provider_repository: ModelProviderRepositoryPort,
    ):
        """Initialize use case with repositories.

        Args:
            model_repository: Model catalog repository
            provider_repository: Provider repository
        """
        self.model_repository = model_repository
        self.provider_repository = provider_repository

    async def execute(
        self,
        provider_id: str,
        model_name: str,
        model_type: str,
        context_limit: int | None = None,
        cost_estimate: float | None = None,
        modalities: list[str] | None = None,
    ) -> Result[ModelCatalog]:
        """Execute model registration.

        Args:
            provider_id: Provider ID
            model_name: Model name
            model_type: Model type
            context_limit: Context limit in tokens
            cost_estimate: Cost per 1M tokens (USD)
            modalities: Supported modalities

        Returns:
            Result with created model or error
        """
        try:
            # Validate provider exists
            provider = await self.provider_repository.get_by_id(provider_id)
            if not provider:
                return Result.failure(
                    NotFoundError("ModelProvider", provider_id)
                )

            # Create model entity
            import uuid

            model = ModelCatalog(
                id=f"mdl-{uuid.uuid4().hex}",
                provider_id=provider_id,
                model_name=model_name,
                type=ModelType(model_type),  # type: ignore
                context_limit=context_limit,
                cost_estimate=cost_estimate,
                modalities=modalities or [],
                active=True,
            )

            # Save via repository
            created = await self.model_repository.create(model)

            return Result.success(created)

        except (ValidationError, NotFoundError) as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("register_model", f"Registration failed: {str(e)}")
            )


class UpdateFeaturePolicyUseCase:
    """Use case for updating feature model policy."""

    def __init__(
        self,
        policy_repository: FeatureModelPolicyRepositoryPort,
        change_log_repository: PolicyChangeLogRepositoryPort,
        version_manager: PolicyVersionManager,
    ):
        """Initialize use case with dependencies.

        Args:
            policy_repository: Policy repository
            change_log_repository: Change log repository
            version_manager: Policy version manager
        """
        self.policy_repository = policy_repository
        self.change_log_repository = change_log_repository
        self.version_manager = version_manager

    async def execute(
        self,
        policy_id: str,
        primary_model_id: str | None = None,
        fallback_model_ids: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        max_cost_per_call: float | None = None,
        max_tokens: int | None = None,
        actor_id: str = "system",
        reason: str = "Policy update",
    ) -> Result[FeatureModelPolicy]:
        """Execute feature policy update.

        Args:
            policy_id: Policy ID to update
            primary_model_id: New primary model ID
            fallback_model_ids: New fallback model IDs
            parameters: New parameters
            max_cost_per_call: New max cost per call
            max_tokens: New max tokens
            actor_id: User making the change
            reason: Reason for the change

        Returns:
            Result with new policy version or error
        """
        try:
            # Prepare new data
            new_data = {}
            if primary_model_id is not None:
                new_data["primary_model_id"] = primary_model_id
            if fallback_model_ids is not None:
                new_data["fallback_model_ids"] = fallback_model_ids
            if parameters is not None:
                new_data["parameters"] = parameters
            if max_cost_per_call is not None:
                new_data["max_cost_per_call"] = max_cost_per_call
            if max_tokens is not None:
                new_data["max_tokens"] = max_tokens

            # Create new version via version manager
            new_policy = await self.version_manager.create_new_version(
                policy_type="feature",
                policy_id=policy_id,
                new_data=new_data,
                actor_id=actor_id,
                reason=reason,
            )

            return Result.success(new_policy)

        except (NotFoundError, ValidationError) as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("update_policy", f"Update failed: {str(e)}")
            )


class RollbackPolicyUseCase:
    """Use case for rolling back policy to previous version."""

    def __init__(
        self,
        policy_repository: FeatureModelPolicyRepositoryPort,
        change_log_repository: PolicyChangeLogRepositoryPort,
        version_manager: PolicyVersionManager,
    ):
        """Initialize use case with dependencies.

        Args:
            policy_repository: Policy repository
            change_log_repository: Change log repository
            version_manager: Policy version manager
        """
        self.policy_repository = policy_repository
        self.change_log_repository = change_log_repository
        self.version_manager = version_manager

    async def execute(
        self,
        policy_type: str,
        policy_id: str,
        target_version: int,
        actor_id: str = "system",
        reason: str = "Rollback",
    ) -> Result[FeatureModelPolicy | PromptPolicy]:
        """Execute policy rollback.

        Args:
            policy_type: Type of policy ("feature" or "prompt")
            policy_id: Policy ID to rollback
            target_version: Version to rollback to
            actor_id: User performing rollback
            reason: Reason for rollback

        Returns:
            Result with rolled-back policy or error
        """
        try:
            # Rollback via version manager
            rolled_back_policy = await self.version_manager.rollback_to_version(
                policy_type=policy_type,
                policy_id=policy_id,
                target_version=target_version,
                actor_id=actor_id,
                reason=reason,
            )

            return Result.success(rolled_back_policy)

        except (NotFoundError, ValidationError) as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("rollback_policy", f"Rollback failed: {str(e)}")
            )


class GetModelMetricsUseCase:
    """Use case for aggregating model invocation metrics."""

    def __init__(
        self,
        invocation_repository: ModelInvocationRepositoryPort,
    ):
        """Initialize use case with repository.

        Args:
            invocation_repository: Invocation repository
        """
        self.invocation_repository = invocation_repository

    async def execute(
        self,
        feature_key: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> Result[dict[str, Any]]:
        """Execute metrics aggregation.

        Args:
            feature_key: Feature to get metrics for
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Result with aggregated metrics or error
        """
        try:
            metrics = await self.invocation_repository.aggregate_metrics(
                feature_key=feature_key,
                start_time=start_time,
                end_time=end_time,
            )

            return Result.success(metrics)

        except Exception as e:
            return Result.failure(
                ValidationError("get_metrics", f"Metrics query failed: {str(e)}")
            )


class ListProvidersUseCase:
    """Use case for listing all providers."""

    def __init__(
        self,
        provider_repository: ModelProviderRepositoryPort,
    ):
        """Initialize use case with repository.

        Args:
            provider_repository: Provider repository
        """
        self.provider_repository = provider_repository

    async def execute(
        self,
        active_only: bool = True,
    ) -> Result[list[ModelProvider]]:
        """Execute provider listing.

        Args:
            active_only: Only list active providers

        Returns:
            Result with list of providers or error
        """
        try:
            providers = await self.provider_repository.list_all(active_only=active_only)
            return Result.success(providers)

        except Exception as e:
            return Result.failure(
                ValidationError("list_providers", f"List failed: {str(e)}")
            )


class ListModelsUseCase:
    """Use case for listing models with filters."""

    def __init__(
        self,
        model_repository: ModelCatalogRepositoryPort,
    ):
        """Initialize use case with repository.

        Args:
            model_repository: Model catalog repository
        """
        self.model_repository = model_repository

    async def execute(
        self,
        provider_id: str | None = None,
        model_type: str | None = None,
        active_only: bool = True,
    ) -> Result[list[ModelCatalog]]:
        """Execute model listing.

        Args:
            provider_id: Filter by provider ID
            model_type: Filter by model type
            active_only: Only list active models

        Returns:
            Result with list of models or error
        """
        try:
            # Convert string to enum if provided
            type_enum = ModelType(model_type) if model_type else None

            models = await self.model_repository.list_all(
                provider_id=provider_id,
                model_type=type_enum,
                active_only=active_only,
            )

            return Result.success(models)

        except (ValidationError, ValueError) as e:
            return Result.failure(
                ValidationError("list_models", f"List failed: {str(e)}")
            )
