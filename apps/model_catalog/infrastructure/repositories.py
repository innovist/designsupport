"""Repository implementations for model catalog.

Implements repository ports using Django ORM.
"""

# @MX:NOTE: Django ORM async operations (asave, aget, etc.) for database I/O
# @MX:REASON: Async repositories support high-concurrency model catalog access
from datetime import datetime
from typing import Any

from django.db.models import Q, Count, Avg, Sum
from django.db.models.functions import TruncDate

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
    PolicyChangeLog,
    PromptPolicy,
)
from apps.model_catalog.infrastructure.orm.models import (
    FeatureModelPolicyModel,
    ModelCatalogModel,
    ModelInvocationModel,
    ModelProviderModel,
    PolicyChangeLogModel,
    PromptPolicyModel,
)


class ModelProviderRepository(ModelProviderRepositoryPort):
    """Django ORM repository for ModelProvider."""

    async def create(self, provider: ModelProvider) -> ModelProvider:
        """Create a new provider."""
        orm_model = ModelProviderModel.from_domain(provider)
        await orm_model.asave()
        return orm_model.to_domain()

    async def get_by_id(self, provider_id: str) -> ModelProvider | None:
        """Get provider by ID."""
        try:
            orm_model = await ModelProviderModel.objects.aget(id=provider_id)
            return orm_model.to_domain()
        except ModelProviderModel.DoesNotExist:
            return None

    async def get_by_name(self, name: str) -> ModelProvider | None:
        """Get provider by name."""
        try:
            orm_model = await ModelProviderModel.objects.aget(name=name)
            return orm_model.to_domain()
        except ModelProviderModel.DoesNotExist:
            return None

    async def list_all(self, active_only: bool = False) -> list[ModelProvider]:
        """List all providers."""
        queryset = ModelProviderModel.objects.all()
        if active_only:
            queryset = queryset.filter(active=True)

        return [m.to_domain() async for m in queryset]

    async def update(self, provider_id: str, **kwargs) -> ModelProvider | None:
        """Update provider fields."""
        try:
            orm_model = await ModelProviderModel.objects.aget(id=provider_id)
            for key, value in kwargs.items():
                if hasattr(orm_model, key):
                    setattr(orm_model, key, value)
            await orm_model.asave()
            return orm_model.to_domain()
        except ModelProviderModel.DoesNotExist:
            return None

    async def deactivate(self, provider_id: str) -> bool:
        """Deactivate a provider."""
        updated = await ModelProviderModel.objects.filter(id=provider_id).aupdate(
            active=False
        )
        return updated > 0


class ModelCatalogRepository(ModelCatalogRepositoryPort):
    """Django ORM repository for ModelCatalog."""

    async def create(self, model: ModelCatalog) -> ModelCatalog:
        """Create a new model catalog entry."""
        orm_model = ModelCatalogModel.from_domain(model)
        await orm_model.asave()
        return orm_model.to_domain()

    async def get_by_id(self, model_id: str) -> ModelCatalog | None:
        """Get model by ID."""
        try:
            orm_model = await ModelCatalogModel.objects.aget(id=model_id)
            return orm_model.to_domain()
        except ModelCatalogModel.DoesNotExist:
            return None

    async def get_provider_by_id(self, provider_id: str) -> ModelProvider | None:
        """Get provider by ID."""
        try:
            orm_model = await ModelProviderModel.objects.aget(id=provider_id)
            return orm_model.to_domain()
        except ModelProviderModel.DoesNotExist:
            return None

    async def get_by_provider(self, provider_id: str) -> list[ModelCatalog]:
        """Get all models for a provider."""
        queryset = ModelCatalogModel.objects.filter(provider_id=provider_id)
        return [m.to_domain() async for m in queryset]

    async def list_by_type(
        self,
        model_type: ModelType,
        active_only: bool = False,
    ) -> list[ModelCatalog]:
        """List models by type."""
        queryset = ModelCatalogModel.objects.filter(type=model_type.value)
        if active_only:
            queryset = queryset.filter(active=True)
        return [m.to_domain() async for m in queryset]

    async def list_all(
        self,
        provider_id: str | None = None,
        model_type: ModelType | None = None,
        active_only: bool = False,
    ) -> list[ModelCatalog]:
        """List models with optional filters."""
        queryset = ModelCatalogModel.objects.all()

        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if model_type:
            queryset = queryset.filter(type=model_type.value)
        if active_only:
            queryset = queryset.filter(active=True)

        return [m.to_domain() async for m in queryset]

    async def update(self, model_id: str, **kwargs) -> ModelCatalog | None:
        """Update model fields."""
        try:
            orm_model = await ModelCatalogModel.objects.aget(id=model_id)
            for key, value in kwargs.items():
                if hasattr(orm_model, key):
                    setattr(orm_model, key, value)
            await orm_model.asave()
            return orm_model.to_domain()
        except ModelCatalogModel.DoesNotExist:
            return None

    async def deactivate(self, model_id: str) -> bool:
        """Deactivate a model."""
        updated = await ModelCatalogModel.objects.filter(id=model_id).aupdate(
            active=False
        )
        return updated > 0


class FeatureModelPolicyRepository(FeatureModelPolicyRepositoryPort):
    """Django ORM repository for FeatureModelPolicy."""

    async def create(self, policy: FeatureModelPolicy) -> FeatureModelPolicy:
        """Create a new feature policy."""
        orm_model = FeatureModelPolicyModel.from_domain(policy)
        await orm_model.asave()

        # Add fallback models
        if policy.fallback_model_ids:
            await orm_model.fallback_models.aset(
                list(await ModelCatalogModel.objects.filter(
                    id__in=policy.fallback_model_ids
                ).all())
            )

        return orm_model.to_domain()

    async def get_by_id(self, policy_id: str) -> FeatureModelPolicy | None:
        """Get policy by ID."""
        try:
            orm_model = await FeatureModelPolicyModel.objects.aget(id=policy_id)
            return orm_model.to_domain()
        except FeatureModelPolicyModel.DoesNotExist:
            return None

    async def get_active_by_feature(self, feature_key: str) -> FeatureModelPolicy | None:
        """Get active policy for a feature."""
        try:
            orm_model = await FeatureModelPolicyModel.objects.filter(
                feature_key=feature_key,
                active=True,
            ).afirst()
            return orm_model.to_domain() if orm_model else None
        except FeatureModelPolicyModel.DoesNotExist:
            return None

    async def list_by_feature(self, feature_key: str) -> list[FeatureModelPolicy]:
        """List all policies for a feature (all versions)."""
        queryset = FeatureModelPolicyModel.objects.filter(
            feature_key=feature_key
        ).order_by("-version")
        return [p.to_domain() async for p in queryset]

    async def list_all(self, active_only: bool = False) -> list[FeatureModelPolicy]:
        """List all policies."""
        queryset = FeatureModelPolicyModel.objects.all()
        if active_only:
            queryset = queryset.filter(active=True)
        return [p.to_domain() async for p in queryset]

    async def get_version(self, policy_id: str, version: int) -> FeatureModelPolicy | None:
        """Get specific version of a policy."""
        try:
            orm_model = await FeatureModelPolicyModel.objects.aget(
                id=policy_id,
                version=version,
            )
            return orm_model.to_domain()
        except FeatureModelPolicyModel.DoesNotExist:
            return None

    async def deactivate(self, policy_id: str) -> bool:
        """Deactivate a policy."""
        updated = await FeatureModelPolicyModel.objects.filter(id=policy_id).aupdate(
            active=False
        )
        return updated > 0


class PromptPolicyRepository(PromptPolicyRepositoryPort):
    """Django ORM repository for PromptPolicy."""

    async def create(self, policy: PromptPolicy) -> PromptPolicy:
        """Create a new prompt policy."""
        orm_model = PromptPolicyModel.from_domain(policy)
        await orm_model.asave()
        return orm_model.to_domain()

    async def get_by_id(self, policy_id: str) -> PromptPolicy | None:
        """Get prompt policy by ID."""
        try:
            orm_model = await PromptPolicyModel.objects.aget(id=policy_id)
            return orm_model.to_domain()
        except PromptPolicyModel.DoesNotExist:
            return None

    async def get_active_by_feature(self, feature_key: str) -> PromptPolicy | None:
        """Get active prompt policy for a feature."""
        try:
            orm_model = await PromptPolicyModel.objects.filter(
                feature_key=feature_key,
                active=True,
            ).afirst()
            return orm_model.to_domain() if orm_model else None
        except PromptPolicyModel.DoesNotExist:
            return None

    async def list_by_feature(self, feature_key: str) -> list[PromptPolicy]:
        """List all prompt policies for a feature."""
        queryset = PromptPolicyModel.objects.filter(
            feature_key=feature_key
        ).order_by("-created_at")
        return [p.to_domain() async for p in queryset]

    async def list_all(self, active_only: bool = False) -> list[PromptPolicy]:
        """List all prompt policies."""
        queryset = PromptPolicyModel.objects.all()
        if active_only:
            queryset = queryset.filter(active=True)
        return [p.to_domain() async for p in queryset]

    async def get_version(self, policy_id: str, version: int) -> PromptPolicy | None:
        """Get specific version of a prompt policy."""
        # Prompt policies don't have version numbers in the same way
        # Use created_at for ordering
        try:
            orm_model = await PromptPolicyModel.objects.filter(
                id=policy_id,
            ).order_by("-created_at")[version]  # type: ignore
            return orm_model.to_domain()
        except (PromptPolicyModel.DoesNotExist, IndexError):
            return None

    async def deactivate(self, policy_id: str) -> bool:
        """Deactivate a prompt policy."""
        updated = await PromptPolicyModel.objects.filter(id=policy_id).aupdate(
            active=False
        )
        return updated > 0


class ModelInvocationRepository(ModelInvocationRepositoryPort):
    """Django ORM repository for ModelInvocation."""

    async def create(self, invocation: ModelInvocation) -> ModelInvocation:
        """Create a new invocation record."""
        orm_model = ModelInvocationModel.from_domain(invocation)
        await orm_model.asave()
        return orm_model.to_domain()

    async def get_by_id(self, invocation_id: str) -> ModelInvocation | None:
        """Get invocation by ID."""
        try:
            orm_model = await ModelInvocationModel.objects.aget(id=invocation_id)
            return orm_model.to_domain()
        except ModelInvocationModel.DoesNotExist:
            return None

    async def list_by_feature(
        self,
        feature_key: str,
        start_time: Any | None = None,
        end_time: Any | None = None,
    ) -> list[ModelInvocation]:
        """List invocations for a feature."""
        queryset = ModelInvocationModel.objects.filter(feature_key=feature_key)

        if start_time:
            queryset = queryset.filter(created_at__gte=start_time)
        if end_time:
            queryset = queryset.filter(created_at__lte=end_time)

        queryset = queryset.order_by("-created_at")
        return [i.to_domain() async for i in queryset]

    async def list_by_session(self, session_id: str) -> list[ModelInvocation]:
        """List invocations for a session."""
        queryset = ModelInvocationModel.objects.filter(
            session_id=session_id
        ).order_by("-created_at")
        return [i.to_domain() async for i in queryset]

    async def aggregate_metrics(
        self,
        feature_key: str,
        start_time: Any | None = None,
        end_time: Any | None = None,
    ) -> dict[str, Any]:
        """Aggregate metrics by feature and time range."""
        queryset = ModelInvocationModel.objects.filter(feature_key=feature_key)

        if start_time:
            queryset = queryset.filter(created_at__gte=start_time)
        if end_time:
            queryset = queryset.filter(created_at__lte=end_time)

        # Aggregate metrics
        aggregation = await queryset.aggregate(
            total_calls=Count("id"),
            success_count=Count("id", filter=Q(status="success")),
            failure_count=Count("id", filter=Q(status="failure")),
            total_tokens_in=Sum("tokens_in"),
            total_tokens_out=Sum("tokens_out"),
            total_cost=Sum("cost_estimate"),
            avg_latency=Avg("latency_ms"),
        )

        # Calculate success rate
        total_calls = aggregation["total_calls"] or 0
        success_count = aggregation["success_count"] or 0
        success_rate = (success_count / total_calls * 100) if total_calls > 0 else 0

        return {
            "feature_key": feature_key,
            "total_calls": total_calls,
            "success_count": success_count,
            "failure_count": aggregation["failure_count"] or 0,
            "success_rate": round(success_rate, 2),
            "total_tokens_in": aggregation["total_tokens_in"] or 0,
            "total_tokens_out": aggregation["total_tokens_out"] or 0,
            "total_cost": float(aggregation["total_cost"] or 0),
            "avg_latency_ms": round(aggregation["avg_latency"] or 0, 2),
            "start_time": start_time,
            "end_time": end_time,
        }


class PolicyChangeLogRepository(PolicyChangeLogRepositoryPort):
    """Django ORM repository for PolicyChangeLog."""

    async def create(self, change_log: PolicyChangeLog) -> PolicyChangeLog:
        """Create a new change log entry."""
        orm_model = PolicyChangeLogModel.from_domain(change_log)
        await orm_model.asave()
        return orm_model.to_domain()

    async def list_by_target(
        self,
        target_type: str,
        target_id: str,
    ) -> list[PolicyChangeLog]:
        """List change logs for a specific policy."""
        queryset = PolicyChangeLogModel.objects.filter(
            target_type=target_type,
            target_id=target_id,
        ).order_by("-created_at")
        return [c.to_domain() async for c in queryset]

    async def list_all(self, limit: int = 100) -> list[PolicyChangeLog]:
        """List recent change logs."""
        queryset = PolicyChangeLogModel.objects.order_by("-created_at")[:limit]
        return [c.to_domain() async for c in queryset]
