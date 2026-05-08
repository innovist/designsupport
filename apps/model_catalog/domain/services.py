"""Domain services for model catalog.

Pure Python domain services with ZERO Django imports.
"""
from datetime import datetime, timezone
from typing import Any

from shared.domain.exceptions import InvariantViolationError, NotFoundError, OperationError

from .entities import (
    FeatureModelPolicy,
    ModelCatalog,
    ModelInvocation,
    PolicyChangeLog,
    PromptPolicy,
)


# @MX:ANCHOR: Central model invocation endpoint for all AI features
# @MX:REASON: Single entry point for model calls, implements fallback chain and cost blocking
class ModelRouter:
    """Domain service for routing model calls with fallback logic.

    Implements REQ-04-ROUTER-001, REQ-04-ROUTER-002, REQ-04-ROUTER-003,
    REQ-04-ROUTER-004, REQ-04-ROUTER-005.
    """

    def __init__(
        self,
        policy_repository,  # Will be injected via ports
        model_repository,  # Will be injected via ports
        invocation_repository,  # Will be injected via ports
        cost_guard,  # CostGuard instance
    ):
        """Initialize model router with required dependencies.

        Args:
            policy_repository: Repository for accessing feature policies
            model_repository: Repository for accessing model catalog
            invocation_repository: Repository for logging invocations
            cost_guard: CostGuard instance for cost checking
        """
        self.policy_repository = policy_repository
        self.model_repository = model_repository
        self.invocation_repository = invocation_repository
        self.cost_guard = cost_guard

    # @MX:WARN: External API calls to model providers with fallback chain
    # @MX:REASON: Multiple sequential HTTP requests can fail; requires proper error handling
    async def invoke(
        self,
        feature_key: str,
        payload: dict[str, Any],
        options: dict[str, Any],
        tenant_id: str,
        workspace_id: str,
        session_id: str | None = None,
    ) -> tuple[Any, ModelInvocation]:
        """Invoke a model for a feature with fallback chain.

        Implements REQ-04-ROUTER-001: Single entry point for model calls.
        Implements REQ-04-ROUTER-002: Primary first, then fallback chain.
        Implements REQ-04-ROUTER-003: NO fake results on failure.
        Implements REQ-04-ROUTER-004: Collect metrics per call.
        Implements REQ-04-ROUTER-005: Block calls exceeding max_cost_per_call.

        Args:
            feature_key: Feature identifier
            payload: Request payload for the model
            options: Additional options (temperature, max_tokens, etc.)
            tenant_id: Tenant identifier
            workspace_id: Workspace identifier
            session_id: Optional session identifier

        Returns:
            Tuple of (model_response, invocation_metrics)

        Raises:
            NotFoundError: If feature policy or models not found
            OperationError: If all models in chain fail
        """
        # Get active policy for feature
        policy = await self.policy_repository.get_active_by_feature(feature_key)
        if not policy:
            raise NotFoundError("FeatureModelPolicy", feature_key)

        # Check cost limit before invoking (REQ-04-ROUTER-005)
        cost_check = await self.cost_guard.check_cost_limit(
            policy_id=policy.id,
            estimated_tokens=options.get("max_tokens", 1000),
        )
        if not cost_check["allowed"]:
            raise OperationError(
                "ModelRouter.invoke",
                f"Cost limit exceeded: {cost_check['reason']}",
            )

        # Try primary model, then fallbacks
        last_error = None
        model_chain = policy.get_model_chain()

        for model_id in model_chain:
            try:
                # Get model details
                model = await self.model_repository.get_by_id(model_id)
                if not model or not model.active:
                    last_error = f"Model {model_id} not found or inactive"
                    continue

                # Invoke model (via provider adapter - to be implemented)
                start_time = datetime.now(timezone.utc)
                response = await self._call_model(model, payload, options)
                end_time = datetime.now(timezone.utc)

                # Calculate metrics (REQ-04-ROUTER-004)
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                tokens_in = response.get("usage", {}).get("prompt_tokens", 0)
                tokens_out = response.get("usage", {}).get("completion_tokens", 0)
                cost_estimate = response.get("usage", {}).get("estimated_cost", 0.0)

                # Create successful invocation record
                invocation = ModelInvocation(
                    id=self._generate_invocation_id(),
                    feature_key=feature_key,
                    tenant_id=tenant_id,
                    workspace_id=workspace_id,
                    session_id=session_id,
                    model_id=model_id,
                    status="success",  # type: ignore
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_estimate=cost_estimate,
                    latency_ms=latency_ms,
                )

                # Log invocation
                await self.invocation_repository.create(invocation)

                return response, invocation

            except Exception as e:
                last_error = str(e)
                # Continue to next model in chain
                continue

        # All models failed (REQ-04-ROUTER-003: NO fake results)
        invocation = ModelInvocation(
            id=self._generate_invocation_id(),
            feature_key=feature_key,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            session_id=session_id,
            model_id=model_chain[0],  # Primary model
            status="failure",  # type: ignore
            error_code="ALL_MODELS_FAILED",
            error_summary=f"All models failed. Last error: {last_error}",
        )

        await self.invocation_repository.create(invocation)

        raise OperationError(
            "ModelRouter.invoke",
            f"ALL_MODELS_FAILED: All models in chain failed for feature {feature_key}",
        )

    async def _call_model(
        self,
        model: ModelCatalog,
        payload: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a specific model via provider adapter.

        Args:
            model: ModelCatalog entity with model details
            payload: Request payload (e.g., {"prompt": "...", "size": "1024x1024"})
            options: Additional options (temperature, max_tokens, etc.)

        Returns:
            Dictionary with:
                - asset_uri: URL/path to generated content
                - cost_meta: CostMetadata instance
                - usage: Token usage data

        Raises:
            OperationError: If provider adapter fails or is not found
        """
        # Get provider information from model repository
        provider = await self.model_repository.get_provider_by_id(model.provider_id)
        if not provider:
            raise OperationError(
                "ModelRouter._call_model",
                f"Provider not found: {model.provider_id}",
            )

        # Import adapters dynamically to avoid circular imports
        try:
            if provider.name == "bytedance":
                from apps.generation.infrastructure.image_providers.seedream_adapter import (
                    SeedreamAdapter,
                )

                adapter = SeedreamAdapter(provider, model)
            elif provider.name == "alibaba":
                from apps.generation.infrastructure.image_providers.alibaba_zimage_adapter import (
                    AlibabaZImageAdapter,
                )

                adapter = AlibabaZImageAdapter(provider, model)
            elif provider.name == "google":
                from apps.generation.infrastructure.image_providers.gemini_image_adapter import (
                    GeminiImageAdapter,
                )

                adapter = GeminiImageAdapter(provider, model)
            elif provider.name == "openai":
                from apps.generation.infrastructure.image_providers.openai_image_adapter import (
                    OpenAIImageAdapter,
                )

                adapter = OpenAIImageAdapter(provider, model)
            else:
                raise OperationError(
                    "ModelRouter._call_model",
                    f"Unsupported provider: {provider.name}",
                )
        except ImportError as e:
            raise OperationError(
                "ModelRouter._call_model",
                f"Failed to import adapter for provider {provider.name}: {str(e)}",
            )

        # Extract parameters from payload
        prompt = payload.get("prompt", "")
        size = payload.get("size", "1024x1024")
        n = payload.get("n", 1)

        # Call adapter
        result = await adapter.generate_image(
            prompt=prompt,
            size=size,
            n=n,
            **options,
        )

        # Check result
        if result.is_failure:
            error = result.error
            if error is not None:
                raise error
            raise OperationError("ModelRouter.invoke", "Unknown error during model invocation")

        # Extract response data
        response_data = result.value

        # Build standardized response
        return {
            "asset_uri": response_data["asset_uri"],
            "cost_meta": response_data["cost_meta"],
            "usage": {
                "prompt_tokens": response_data["cost_meta"].prompt_tokens,
                "completion_tokens": response_data["cost_meta"].completion_tokens,
                "total_tokens": response_data["cost_meta"].total_tokens,
                "estimated_cost": response_data["cost_meta"].cost_usd,
            },
        }

    def _generate_invocation_id(self) -> str:
        """Generate unique invocation ID."""
        import uuid

        return f"inv-{uuid.uuid4().hex}"


# @MX:ANCHOR: Policy versioning for feature and prompt policies
# @MX:REASON: Central policy management; used by admin console and API endpoints
class PolicyVersionManager:
    """Domain service for managing policy versioning.

    Implements REQ-04-POLICY-004: Policy changes create new version.
    """

    def __init__(self, policy_repository, change_log_repository):
        """Initialize policy version manager.

        Args:
            policy_repository: Repository for policy CRUD
            change_log_repository: Repository for change logging
        """
        self.policy_repository = policy_repository
        self.change_log_repository = change_log_repository

    async def create_new_version(
        self,
        policy_type: str,  # "feature" or "prompt"
        policy_id: str,
        new_data: dict[str, Any],
        actor_id: str,
        reason: str,
    ) -> FeatureModelPolicy | PromptPolicy:
        """Create a new version of a policy.

        Implements REQ-04-POLICY-004: Create new version, deactivate old.
        Implements REQ-04-POLICY-005: Log all changes with actor/target/diff.

        Args:
            policy_type: Type of policy ("feature" or "prompt")
            policy_id: ID of policy to version
            new_data: New policy data
            actor_id: User creating the new version
            reason: Reason for the change

        Returns:
            Newly created policy version

        Raises:
            NotFoundError: If policy not found
        """
        # Get current policy
        if policy_type == "feature":
            current_policy = await self.policy_repository.get_by_id(policy_id)
            if not current_policy:
                raise NotFoundError("FeatureModelPolicy", policy_id)

            # Deactivate current version
            updated_policy = FeatureModelPolicy(
                id=current_policy.id,
                feature_key=current_policy.feature_key,
                primary_model_id=new_data.get("primary_model_id", current_policy.primary_model_id),
                fallback_model_ids=new_data.get("fallback_model_ids", current_policy.fallback_model_ids),
                parameters=new_data.get("parameters", current_policy.parameters),
                max_cost_per_call=new_data.get("max_cost_per_call", current_policy.max_cost_per_call),
                max_tokens=new_data.get("max_tokens", current_policy.max_tokens),
                version=current_policy.version + 1,
                active=True,
                reviewer=actor_id,
                created_at=datetime.now(timezone.utc),
            )

            # Create new version
            new_policy = await self.policy_repository.create(updated_policy)

            # Deactivate old version
            await self.policy_repository.deactivate(current_policy.id)

        elif policy_type == "prompt":
            # Similar logic for PromptPolicy
            current_policy = await self.policy_repository.get_prompt_by_id(policy_id)
            if not current_policy:
                raise NotFoundError("PromptPolicy", policy_id)

            updated_policy = PromptPolicy(
                id=current_policy.id,
                feature_key=current_policy.feature_key,
                prompt_version=new_data.get("prompt_version", current_policy.prompt_version),
                system_prompt=new_data.get("system_prompt", current_policy.system_prompt),
                user_template=new_data.get("user_template", current_policy.user_template),
                active=True,
                reviewer=actor_id,
                created_at=datetime.now(timezone.utc),
            )

            new_policy = await self.policy_repository.create_prompt(updated_policy)
            await self.policy_repository.deactivate_prompt(current_policy.id)

        else:
            raise InvariantViolationError(f"Invalid policy type: {policy_type}")

        # Log the change (REQ-04-POLICY-005)
        version_from = getattr(current_policy, 'version', 0)
        version_to = getattr(updated_policy, 'version', version_from + 1)
        change_log = PolicyChangeLog(
            id=self._generate_change_log_id(),
            target_type=policy_type,
            target_id=policy_id,
            version_from=version_from,
            version_to=version_to,
            actor_id=actor_id,
            reason=reason,
            created_at=datetime.now(timezone.utc),
        )

        await self.change_log_repository.create(change_log)

        return new_policy

    async def rollback_to_version(
        self,
        policy_type: str,
        policy_id: str,
        target_version: int,
        actor_id: str,
        reason: str,
    ) -> FeatureModelPolicy | PromptPolicy:
        """Rollback a policy to a specific version.

        Args:
            policy_type: Type of policy ("feature" or "prompt")
            policy_id: ID of policy to rollback
            target_version: Version to rollback to
            actor_id: User performing the rollback
            reason: Reason for the rollback

        Returns:
            Reactivated policy version

        Raises:
            NotFoundError: If version not found
        """
        # Get target version
        if policy_type == "feature":
            target_policy = await self.policy_repository.get_version(policy_id, target_version)
            if not target_policy:
                raise NotFoundError("FeatureModelPolicy", f"version {target_version}")

            # Deactivate current version
            current_policy = await self.policy_repository.get_active_by_feature(
                target_policy.feature_key
            )
            if current_policy:
                await self.policy_repository.deactivate(current_policy.id)

            # Activate target version (create new version with same data)
            rollback_policy = FeatureModelPolicy(
                id=target_policy.id,
                feature_key=target_policy.feature_key,
                primary_model_id=target_policy.primary_model_id,
                fallback_model_ids=target_policy.fallback_model_ids,
                parameters=target_policy.parameters,
                max_cost_per_call=target_policy.max_cost_per_call,
                max_tokens=target_policy.max_tokens,
                version=target_policy.version + 1,  # New version number
                active=True,
                reviewer=actor_id,
                created_at=datetime.now(timezone.utc),
            )

            new_policy = await self.policy_repository.create(rollback_policy)

        else:
            # Similar logic for PromptPolicy
            target_policy = await self.policy_repository.get_prompt_version(policy_id, target_version)
            if not target_policy:
                raise NotFoundError("PromptPolicy", f"version {target_version}")

            current_policy = await self.policy_repository.get_active_prompt_by_feature(
                target_policy.feature_key
            )
            if current_policy:
                await self.policy_repository.deactivate_prompt(current_policy.id)

            rollback_policy = PromptPolicy(
                id=target_policy.id,
                feature_key=target_policy.feature_key,
                prompt_version=target_policy.prompt_version,
                system_prompt=target_policy.system_prompt,
                user_template=target_policy.user_template,
                active=True,
                reviewer=actor_id,
                created_at=datetime.now(timezone.utc),
            )

            new_policy = await self.policy_repository.create_prompt(rollback_policy)

        # Log the rollback
        version_from = getattr(current_policy, 'version', 0) if current_policy else 0
        version_to = getattr(rollback_policy, 'version', version_from)
        change_log = PolicyChangeLog(
            id=self._generate_change_log_id(),
            target_type=policy_type,
            target_id=policy_id,
            version_from=version_from,
            version_to=version_to,
            actor_id=actor_id,
            reason=f"Rollback: {reason}",
            created_at=datetime.now(timezone.utc),
        )

        await self.change_log_repository.create(change_log)

        return new_policy

    def _generate_change_log_id(self) -> str:
        """Generate unique change log ID."""
        import uuid

        return f"chg-{uuid.uuid4().hex}"


# @MX:WARN: CostGuard check; incorrect policy can block all model invocations
# @MX:REASON: Cost calculation errors cause false positives, blocking legitimate calls
class CostGuard:
    """Domain service for cost estimation and blocking.

    Implements REQ-04-ROUTER-005: Block calls exceeding max_cost_per_call.
    """

    def __init__(
        self,
        policy_repository,  # Will be injected via ports
    ):
        """Initialize cost guard with policy repository.

        Args:
            policy_repository: Repository for accessing feature policies
        """
        self.policy_repository = policy_repository

    async def check_cost_limit(
        self,
        policy_id: str,
        estimated_tokens: int,
    ) -> dict[str, Any]:
        """Check if a call would exceed cost limits.

        Args:
            policy_id: ID of the feature policy to check
            estimated_tokens: Estimated tokens for the call

        Returns:
            Dictionary with:
                - allowed (bool): Whether call is allowed
                - reason (str | None): Reason if not allowed

        Raises:
            NotFoundError: If policy not found
        """
        # Get policy to check max_cost_per_call
        policy = await self.policy_repository.get_by_id(policy_id)
        if not policy:
            from shared.domain.exceptions import NotFoundError

            raise NotFoundError("FeatureModelPolicy", policy_id)

        # If no max_cost_per_call set, allow all calls
        if policy.max_cost_per_call is None:
            return {
                "allowed": True,
                "reason": None,
            }

        # Get primary model to estimate cost
        model = await self.policy_repository.model_repository.get_by_id(
            policy.primary_model_id
        )
        if not model or model.cost_estimate is None:
            # Cannot estimate cost, allow with warning
            return {
                "allowed": True,
                "reason": None,
            }

        # Estimate cost based on model's cost per 1M tokens
        estimated_cost = (estimated_tokens / 1_000_000) * model.cost_estimate

        # Check if estimated cost exceeds max_cost_per_call
        if estimated_cost > policy.max_cost_per_call:
            return {
                "allowed": False,
                "reason": (
                    f"Estimated cost ${estimated_cost:.4f} exceeds "
                    f"max_cost_per_call ${policy.max_cost_per_call:.4f}"
                ),
            }

        return {
            "allowed": True,
            "reason": None,
        }
