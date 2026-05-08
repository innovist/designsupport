"""Repository implementations for admin console infrastructure layer.

Implements ports defined in application layer using Django ORM.
"""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from apps.admin_console.application.ports import (
    AuditLogPort,
    JobQueuePort,
    MetricsPort,
    ModelCatalogPort,
    PolicyChangeLogPort,
    PolicyPort,
    UserManagementPort,
)
from apps.admin_console.domain.entities import (
    AdminSession,
    AdminRole,
    MetricsSummary,
    PolicyChangeLogEntry,
)
from apps.admin_console.domain.value_objects import (
    AuditLogFilter,
    FallbackChain,
    JobQueueFilter,
)
from apps.admin_console.infrastructure.orm.models import (
    AdminMetricsORM,
    AdminSessionORM,
    FeaturePolicyORM,
    PolicyChangeLogORM,
    PromptPolicyORM,
    TenantORM,
    UserTenantRoleORM,
)
from apps.model_catalog.infrastructure.orm.models import (
    ModelCatalogModel as ModelCatalogORM,
)
from apps.model_catalog.infrastructure.orm.models import (
    ModelProviderModel as ModelProviderORM,
)
from django.db import models as django_models
from django.db.models import Q, Count, Sum, Avg, F, FloatField, DecimalField
from django.db.models.functions import Cast
from shared.application.result import Result
from shared.domain.exceptions import DomainError, NotFoundError, ValidationError


# @MX:ANCHOR: Model Catalog Repository - Primary data access for model providers and catalogs
# @MX:REASON: Implements core model catalog operations used by multiple admin features
class ModelCatalogRepository(ModelCatalogPort):
    """Django ORM implementation of model catalog port."""

    async def list_providers(
        self, session: AdminSession
    ) -> Result[list[dict]]:
        """List all model providers."""
        try:
            queryset = ModelProviderORM.objects.all()
            providers = [
                {
                    "id": p.id,
                    "name": p.name,
                    "api_key_env": p.api_key_env,
                    "base_url": p.base_url,
                    "endpoint_path": p.endpoint_path,
                    "auth_scheme": p.auth_scheme,
                    "active": p.active,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat(),
                    "model_count": p.models.count(),
                }
                for p in queryset
            ]
            return Result.success(providers)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to list providers: {str(e)}"))

    async def get_provider(
        self, provider_id: str, session: AdminSession
    ) -> Result[dict]:
        """Get provider details."""
        try:
            provider = ModelProviderORM.objects.get(id=provider_id)
            return Result.success({
                "id": provider.id,
                "name": provider.name,
                "api_key_env": provider.api_key_env,
                "base_url": provider.base_url,
                "endpoint_path": provider.endpoint_path,
                "auth_scheme": provider.auth_scheme,
                "active": provider.active,
                "created_at": provider.created_at.isoformat(),
                "updated_at": provider.updated_at.isoformat(),
                "models": [
                    {
                        "id": m.id,
                        "model_name": m.model_name,
                        "type": m.type,
                        "active": m.active,
                    }
                    for m in provider.models.all()
                ],
            })
        except ModelProviderORM.DoesNotExist:
            return Result.failure(NotFoundError("Provider", provider_id))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get provider: {str(e)}"))

    async def create_provider(
        self, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Create new provider."""
        try:
            provider = ModelProviderORM.objects.create(
                id=data.get("id", data["name"].lower().replace("-", "_")),
                name=data["name"],
                api_key_env=data["api_key_env"],
                base_url=data.get("base_url"),
                endpoint_path=data.get("endpoint_path"),
                auth_scheme=data.get("auth_scheme", "Bearer"),
            )
            return Result.success({
                "id": provider.id,
                "name": provider.name,
                "active": provider.active,
                "created_at": provider.created_at.isoformat(),
            })
        except django_models.IntegrityError:
            return Result.failure(ValidationError("name", f"Provider already exists: {data['name']}"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to create provider: {str(e)}"))

    async def update_provider(
        self, provider_id: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update provider."""
        try:
            provider = ModelProviderORM.objects.get(id=provider_id)
            if "name" in data:
                provider.name = data["name"]
            if "api_key_env" in data:
                provider.api_key_env = data["api_key_env"]
            if "base_url" in data:
                provider.base_url = data["base_url"]
            if "endpoint_path" in data:
                provider.endpoint_path = data["endpoint_path"]
            if "auth_scheme" in data:
                provider.auth_scheme = data["auth_scheme"]
            if "active" in data:
                provider.active = data["active"]
            provider.save()
            return Result.success({
                "id": provider.id,
                "name": provider.name,
                "active": provider.active,
                "updated_at": provider.updated_at.isoformat(),
            })
        except ModelProviderORM.DoesNotExist:
            return Result.failure(NotFoundError("Provider", provider_id))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to update provider: {str(e)}"))

    async def deactivate_provider(
        self, provider_id: str, session: AdminSession
    ) -> Result[None]:
        """Deactivate provider."""
        try:
            provider = ModelProviderORM.objects.get(id=provider_id)
            provider.active = False
            provider.save()
            return Result.success(None)
        except ModelProviderORM.DoesNotExist:
            return Result.failure(NotFoundError("Provider", provider_id))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to deactivate provider: {str(e)}"))

    async def list_models(self, session: AdminSession) -> Result[list[dict]]:
        """List all models."""
        try:
            queryset = ModelCatalogORM.objects.select_related("provider").all()
            models_list = [
                {
                    "id": m.id,
                    "provider": m.provider.name,
                    "provider_id": m.provider.id,
                    "model_name": m.model_name,
                    "type": m.type,
                    "context_limit": m.context_limit,
                    "cost_estimate": float(m.cost_estimate) if m.cost_estimate else None,
                    "modalities": m.modalities,
                    "active": m.active,
                    "created_at": m.created_at.isoformat(),
                }
                for m in queryset
            ]
            return Result.success(models_list)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to list models: {str(e)}"),
            )

    async def get_model(
        self, model_id: str, session: AdminSession
    ) -> Result[dict]:
        """Get model details."""
        try:
            model = ModelCatalogORM.objects.select_related("provider").get(id=model_id)
            return Result.success({
                "id": model.id,
                "provider": model.provider.name,
                "provider_id": model.provider.id,
                "model_name": model.model_name,
                "type": model.type,
                "context_limit": model.context_limit,
                "cost_estimate": float(model.cost_estimate) if model.cost_estimate else None,
                "modalities": model.modalities,
                "active": model.active,
                "created_at": model.created_at.isoformat(),
                "updated_at": model.updated_at.isoformat(),
            })
        except ModelCatalogORM.DoesNotExist:
            return Result.failure(DomainError(f"Model {model_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get model: {str(e)}"),
            )

    async def create_model(self, data: dict, session: AdminSession) -> Result[dict]:
        """Create new model."""
        try:
            model = ModelCatalogORM.objects.create(
                id=data.get("id", f"{data['provider_id']}_{data['model_name'].lower().replace('-', '_')}"),
                provider_id=data["provider_id"],
                model_name=data["model_name"],
                type=data["type"],
                context_limit=data.get("context_limit"),
                cost_estimate=data.get("cost_estimate"),
                modalities=data.get("modalities", []),
            )
            return Result.success({
                "id": model.id,
                "model_name": model.model_name,
                "type": model.type,
                "active": model.active,
                "created_at": model.created_at.isoformat(),
            })
        except django_models.IntegrityError:
            return Result.failure(DomainError(f"Model already exists for provider {data['provider_id']}"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to create model: {str(e)}"),
            )

    async def update_model(
        self, model_id: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update model."""
        try:
            model = ModelCatalogORM.objects.get(id=model_id)
            if "model_name" in data:
                model.model_name = data["model_name"]
            if "type" in data:
                model.type = data["type"]
            if "context_limit" in data:
                model.context_limit = data["context_limit"]
            if "cost_estimate" in data:
                model.cost_estimate = data["cost_estimate"]
            if "modalities" in data:
                model.modalities = data["modalities"]
            if "active" in data:
                model.active = data["active"]
            model.save()
            return Result.success({
                "id": model.id,
                "model_name": model.model_name,
                "type": model.type,
                "active": model.active,
                "updated_at": model.updated_at.isoformat(),
            })
        except ModelCatalogORM.DoesNotExist:
            return Result.failure(DomainError(f"Model {model_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to update model: {str(e)}"),
            )

    async def deactivate_model(
        self, model_id: str, session: AdminSession
    ) -> Result[None]:
        """Deactivate model."""
        try:
            model = ModelCatalogORM.objects.get(id=model_id)
            model.active = False
            model.save()
            return Result.success(None)
        except ModelCatalogORM.DoesNotExist:
            return Result.failure(DomainError(f"Model {model_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to deactivate model: {str(e)}"),
            )


# @MX:ANCHOR: Policy Repository - Manages feature and prompt policy versions
# @MX:REASON: Central policy management used by multiple admin features
class PolicyRepository(PolicyPort):
    """Django ORM implementation of policy port."""

    async def list_feature_policies(
        self, session: AdminSession
    ) -> Result[list[dict]]:
        """List all feature policies."""
        try:
            # Get latest version of each policy
            latest_policies = (
                FeaturePolicyORM.objects.filter(is_active=True)
                .values("feature_key")
                .annotate(max_version=Count("version"))
                .order_by("feature_key")
            )

            policies = []
            for item in latest_policies:
                policy = FeaturePolicyORM.objects.filter(
                    feature_key=item["feature_key"],
                    version=item["max_version"],
                    is_active=True,
                ).first()

                if policy:
                    policies.append({
                        "id": str(policy.id),
                        "feature_key": policy.feature_key,
                        "version": policy.version,
                        "is_active": policy.is_active,
                        "model_type": policy.model_type,
                        "primary_model": policy.primary_model,
                        "fallback_models": policy.fallback_models,
                        "max_retries": policy.max_retries,
                        "timeout_seconds": policy.timeout_seconds,
                        "max_cost_per_request": float(policy.max_cost_per_request),
                        "max_cost_per_day": float(policy.max_cost_per_day),
                        "max_cost_per_month": float(policy.max_cost_per_month),
                        "currency": policy.currency,
                        "required_model_types": policy.required_model_types,
                        "min_context_length": policy.min_context_length,
                        "supports_streaming": policy.supports_streaming,
                        "supports_function_calling": policy.supports_function_calling,
                        "max_tokens_per_request": policy.max_tokens_per_request,
                        "created_at": policy.created_at.isoformat(),
                        "updated_at": policy.updated_at.isoformat(),
                    })

            return Result.success(policies)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to list feature policies: {str(e)}"),
            )

    async def get_feature_policy(
        self, feature_key: str, version: int | None, session: AdminSession
    ) -> Result[dict]:
        """Get feature policy with version history."""
        try:
            queryset = FeaturePolicyORM.objects.filter(feature_key=feature_key)
            if version is not None:
                queryset = queryset.filter(version=version)

            policy = queryset.order_by("-version").first()

            if not policy:
                return Result.failure(DomainError(f"Feature policy {feature_key} not found"))

            # Get version history
            history = list(
                FeaturePolicyORM.objects.filter(
                    feature_key=feature_key
                ).order_by("-version").values(
                    "version", "is_active", "created_at", "created_by", "change_reason"
                )
            )

            return Result.success({
                "id": str(policy.id),
                "feature_key": policy.feature_key,
                "version": policy.version,
                "is_active": policy.is_active,
                "model_type": policy.model_type,
                "primary_model": policy.primary_model,
                "fallback_models": policy.fallback_models,
                "max_retries": policy.max_retries,
                "timeout_seconds": policy.timeout_seconds,
                "max_cost_per_request": float(policy.max_cost_per_request),
                "max_cost_per_day": float(policy.max_cost_per_day),
                "max_cost_per_month": float(policy.max_cost_per_month),
                "currency": policy.currency,
                "required_model_types": policy.required_model_types,
                "min_context_length": policy.min_context_length,
                "supports_streaming": policy.supports_streaming,
                "supports_function_calling": policy.supports_function_calling,
                "max_tokens_per_request": policy.max_tokens_per_request,
                "created_at": policy.created_at.isoformat(),
                "updated_at": policy.updated_at.isoformat(),
                "created_by": policy.created_by,
                "modified_by": policy.modified_by,
                "change_reason": policy.change_reason,
                "history": history,
            })
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get feature policy: {str(e)}"),
            )

    async def create_feature_policy(
        self, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Create new feature policy."""
        try:
            policy = FeaturePolicyORM.objects.create(
                id=uuid4(),
                feature_key=data["feature_key"],
                version=1,
                model_type=data["model_type"],
                primary_model=data["primary_model"],
                fallback_models=data.get("fallback_models", []),
                max_retries=data.get("max_retries", 3),
                timeout_seconds=data.get("timeout_seconds", 30),
                max_cost_per_request=data["max_cost_per_request"],
                max_cost_per_day=data["max_cost_per_day"],
                max_cost_per_month=data["max_cost_per_month"],
                currency=data.get("currency", "USD"),
                required_model_types=data.get("required_model_types", []),
                min_context_length=data.get("min_context_length", 4096),
                supports_streaming=data.get("supports_streaming", False),
                supports_function_calling=data.get("supports_function_calling", False),
                max_tokens_per_request=data.get("max_tokens_per_request", 4096),
                created_by=session.user_id,
                modified_by=session.user_id,
                change_reason=data.get("change_reason", "Initial creation"),
            )
            return Result.success({
                "id": str(policy.id),
                "feature_key": policy.feature_key,
                "version": policy.version,
                "created_at": policy.created_at.isoformat(),
            })
        except django_models.IntegrityError:
            return Result.failure(DomainError(f"Feature policy {data['feature_key']} already exists"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to create feature policy: {str(e)}"),
            )

    async def update_feature_policy(
        self, feature_key: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update feature policy (creates new version)."""
        try:
            # Get latest version
            latest = FeaturePolicyORM.objects.filter(
                feature_key=feature_key
            ).order_by("-version").first()

            if not latest:
                return Result.failure(DomainError(f"Feature policy {feature_key} not found"))

            new_version = latest.version + 1

            # Deactivate old version
            latest.is_active = False
            latest.save()

            # Create new version
            policy = FeaturePolicyORM.objects.create(
                id=uuid4(),
                feature_key=feature_key,
                version=new_version,
                model_type=data.get("model_type", latest.model_type),
                primary_model=data.get("primary_model", latest.primary_model),
                fallback_models=data.get("fallback_models", latest.fallback_models),
                max_retries=data.get("max_retries", latest.max_retries),
                timeout_seconds=data.get("timeout_seconds", latest.timeout_seconds),
                max_cost_per_request=data.get(
                    "max_cost_per_request", latest.max_cost_per_request
                ),
                max_cost_per_day=data.get("max_cost_per_day", latest.max_cost_per_day),
                max_cost_per_month=data.get(
                    "max_cost_per_month", latest.max_cost_per_month
                ),
                currency=data.get("currency", latest.currency),
                required_model_types=data.get(
                    "required_model_types", latest.required_model_types
                ),
                min_context_length=data.get(
                    "min_context_length", latest.min_context_length
                ),
                supports_streaming=data.get(
                    "supports_streaming", latest.supports_streaming
                ),
                supports_function_calling=data.get(
                    "supports_function_calling", latest.supports_function_calling
                ),
                max_tokens_per_request=data.get(
                    "max_tokens_per_request", latest.max_tokens_per_request
                ),
                created_by=latest.created_by,
                modified_by=session.user_id,
                change_reason=data.get("change_reason", "Policy update"),
            )

            return Result.success({
                "id": str(policy.id),
                "feature_key": policy.feature_key,
                "version": policy.version,
                "created_at": policy.created_at.isoformat(),
            })
        except Exception as e:
            return Result.failure(DomainError(f"Failed to update feature policy: {str(e)}"),
            )

    async def rollback_feature_policy(
        self,
        feature_key: str,
        to_version: int,
        reason: str,
        session: AdminSession,
    ) -> Result[dict]:
        """Rollback feature policy to previous version."""
        try:
            # Get current active version
            current = FeaturePolicyORM.objects.filter(
                feature_key=feature_key, is_active=True
            ).first()

            if not current:
                return Result.failure(DomainError(f"No active policy found for {feature_key}"))

            # Get target version
            target = FeaturePolicyORM.objects.filter(
                feature_key=feature_key, version=to_version
            ).first()

            if not target:
                return Result.failure(DomainError(f"Version {to_version} not found for {feature_key}"))

            # Deactivate current version
            current.is_active = False
            current.save()

            # Create new version from target
            new_version = (
                FeaturePolicyORM.objects.filter(feature_key=feature_key).aggregate(
                    max_version=Count("version")
                )["max_version"]
                or 0
            ) + 1

            policy = FeaturePolicyORM.objects.create(
                id=uuid4(),
                feature_key=feature_key,
                version=new_version,
                model_type=target.model_type,
                primary_model=target.primary_model,
                fallback_models=target.fallback_models,
                max_retries=target.max_retries,
                timeout_seconds=target.timeout_seconds,
                max_cost_per_request=target.max_cost_per_request,
                max_cost_per_day=target.max_cost_per_day,
                max_cost_per_month=target.max_cost_per_month,
                currency=target.currency,
                required_model_types=target.required_model_types,
                min_context_length=target.min_context_length,
                supports_streaming=target.supports_streaming,
                supports_function_calling=target.supports_function_calling,
                max_tokens_per_request=target.max_tokens_per_request,
                created_by=target.created_by,
                modified_by=session.user_id,
                change_reason=f"Rollback to v{to_version}: {reason}",
            )

            return Result.success({
                "id": str(policy.id),
                "feature_key": policy.feature_key,
                "version": policy.version,
                "rolled_back_from": to_version,
                "created_at": policy.created_at.isoformat(),
            })
        except Exception as e:
            return Result.failure(DomainError(f"Failed to rollback feature policy: {str(e)}"),
            )

    async def list_prompt_policies(
        self, session: AdminSession
    ) -> Result[list[dict]]:
        """List all prompt policies."""
        try:
            policies = PromptPolicyORM.objects.filter(is_active=True).order_by(
                "feature_key"
            )
            result = [
                {
                    "id": str(p.id),
                    "feature_key": p.feature_key,
                    "version": p.version,
                    "is_active": p.is_active,
                    "temperature": p.temperature,
                    "max_tokens": p.max_tokens,
                    "top_p": p.top_p,
                    "frequency_penalty": p.frequency_penalty,
                    "presence_penalty": p.presence_penalty,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat(),
                }
                for p in policies
            ]
            return Result.success(result)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to list prompt policies: {str(e)}"),
            )

    async def get_prompt_policy(
        self, feature_key: str, version: int | None, session: AdminSession
    ) -> Result[dict]:
        """Get prompt policy with version history."""
        try:
            queryset = PromptPolicyORM.objects.filter(feature_key=feature_key)
            if version is not None:
                queryset = queryset.filter(version=version)

            policy = queryset.order_by("-version").first()

            if not policy:
                return Result.failure(DomainError(f"Prompt policy {feature_key} not found"))

            # Get version history
            history = list(
                PromptPolicyORM.objects.filter(
                    feature_key=feature_key
                ).order_by("-version").values(
                    "version", "is_active", "created_at", "created_by", "change_reason"
                )
            )

            return Result.success({
                "id": str(policy.id),
                "feature_key": policy.feature_key,
                "version": policy.version,
                "is_active": policy.is_active,
                "system_prompt": policy.system_prompt,
                "user_template": policy.user_template,
                "temperature": policy.temperature,
                "max_tokens": policy.max_tokens,
                "top_p": policy.top_p,
                "frequency_penalty": policy.frequency_penalty,
                "presence_penalty": policy.presence_penalty,
                "created_at": policy.created_at.isoformat(),
                "updated_at": policy.updated_at.isoformat(),
                "created_by": policy.created_by,
                "modified_by": policy.modified_by,
                "change_reason": policy.change_reason,
                "history": history,
            })
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get prompt policy: {str(e)}"),
            )

    async def update_prompt_policy(
        self, feature_key: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update prompt policy (creates new version)."""
        try:
            # Get latest version
            latest = PromptPolicyORM.objects.filter(
                feature_key=feature_key
            ).order_by("-version").first()

            if not latest:
                return Result.failure(DomainError(f"Prompt policy {feature_key} not found"))

            new_version = latest.version + 1

            # Deactivate old version
            latest.is_active = False
            latest.save()

            # Create new version
            policy = PromptPolicyORM.objects.create(
                id=uuid4(),
                feature_key=feature_key,
                version=new_version,
                system_prompt=data.get("system_prompt", latest.system_prompt),
                user_template=data.get("user_template", latest.user_template),
                temperature=data.get("temperature", latest.temperature),
                max_tokens=data.get("max_tokens", latest.max_tokens),
                top_p=data.get("top_p", latest.top_p),
                frequency_penalty=data.get(
                    "frequency_penalty", latest.frequency_penalty
                ),
                presence_penalty=data.get("presence_penalty", latest.presence_penalty),
                created_by=latest.created_by,
                modified_by=session.user_id,
                change_reason=data.get("change_reason", "Policy update"),
            )

            return Result.success({
                "id": str(policy.id),
                "feature_key": policy.feature_key,
                "version": policy.version,
                "created_at": policy.created_at.isoformat(),
            })
        except Exception as e:
            return Result.failure(DomainError(f"Failed to update prompt policy: {str(e)}"),
            )

    async def rollback_prompt_policy(
        self,
        feature_key: str,
        to_version: int,
        reason: str,
        session: AdminSession,
    ) -> Result[dict]:
        """Rollback prompt policy to previous version."""
        try:
            # Get current active version
            current = PromptPolicyORM.objects.filter(
                feature_key=feature_key, is_active=True
            ).first()

            if not current:
                return Result.failure(DomainError(f"No active policy found for {feature_key}"))

            # Get target version
            target = PromptPolicyORM.objects.filter(
                feature_key=feature_key, version=to_version
            ).first()

            if not target:
                return Result.failure(DomainError(f"Version {to_version} not found for {feature_key}"))

            # Deactivate current version
            current.is_active = False
            current.save()

            # Create new version from target
            new_version = (
                PromptPolicyORM.objects.filter(feature_key=feature_key).aggregate(
                    max_version=Count("version")
                )["max_version"]
                or 0
            ) + 1

            policy = PromptPolicyORM.objects.create(
                id=uuid4(),
                feature_key=feature_key,
                version=new_version,
                system_prompt=target.system_prompt,
                user_template=target.user_template,
                temperature=target.temperature,
                max_tokens=target.max_tokens,
                top_p=target.top_p,
                frequency_penalty=target.frequency_penalty,
                presence_penalty=target.presence_penalty,
                created_by=target.created_by,
                modified_by=session.user_id,
                change_reason=f"Rollback to v{to_version}: {reason}",
            )

            return Result.success({
                "id": str(policy.id),
                "feature_key": policy.feature_key,
                "version": policy.version,
                "rolled_back_from": to_version,
                "created_at": policy.created_at.isoformat(),
            })
        except Exception as e:
            return Result.failure(DomainError(f"Failed to rollback prompt policy: {str(e)}"),
            )

    async def get_policy_history(
        self, policy_id: str, session: AdminSession
    ) -> Result[list[PolicyChangeLogEntry]]:
        """Get policy version history."""
        try:
            logs = PolicyChangeLogORM.objects.filter(
                policy_id=policy_id
            ).order_by("-created_at")

            entries = [log.to_domain() for log in logs]
            return Result.success(entries)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get policy history: {str(e)}"),
            )


class AuditLogRepository(AuditLogPort):
    """Django ORM implementation of audit log port."""

    async def search_audit_logs(
        self, filters: AuditLogFilter, session: AdminSession
    ) -> Result[list[dict]]:
        """Search audit logs with filters."""
        try:
            # This is a placeholder - actual audit logs would be in a separate table
            # For now, return policy change logs as audit logs
            queryset = PolicyChangeLogORM.objects.all()

            if filters.actor_id:
                queryset = queryset.filter(changed_by=filters.actor_id)
            if filters.start_date:
                start = datetime.fromisoformat(filters.start_date)
                queryset = queryset.filter(created_at__gte=start)
            if filters.end_date:
                end = datetime.fromisoformat(filters.end_date)
                queryset = queryset.filter(created_at__lte=end)

            logs = queryset.order_by("-created_at")[
                filters.offset : filters.offset + filters.limit
            ]

            result = [
                {
                    "id": str(log.id),
                    "policy_id": log.policy_id,
                    "policy_type": log.policy_type,
                    "version": log.version,
                    "changed_by": str(log.changed_by),
                    "change_type": log.change_type,
                    "previous_version": log.previous_version,
                    "change_summary": log.change_summary,
                    "change_details": log.change_details,
                    "timestamp": log.created_at.isoformat(),
                }
                for log in logs
            ]
            return Result.success(result)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to search audit logs: {str(e)}"),
            )

    async def get_audit_log_detail(
        self, log_id: UUID, session: AdminSession
    ) -> Result[dict]:
        """Get audit log detail."""
        try:
            log = PolicyChangeLogORM.objects.get(id=log_id)
            return Result.success({
                "id": str(log.id),
                "policy_id": log.policy_id,
                "policy_type": log.policy_type,
                "version": log.version,
                "changed_by": str(log.changed_by),
                "change_type": log.change_type,
                "previous_version": log.previous_version,
                "change_summary": log.change_summary,
                "change_details": log.change_details,
                "timestamp": log.created_at.isoformat(),
            })
        except PolicyChangeLogORM.DoesNotExist:
            return Result.failure(DomainError(f"Audit log {log_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get audit log detail: {str(e)}"),
            )


class MetricsRepository(MetricsPort):
    """Django ORM implementation of metrics port."""

    async def get_metrics_summary(
        self,
        period: str,
        start_date: str,
        end_date: str,
        feature_key: str | None,
        session: AdminSession,
    ) -> Result[MetricsSummary]:
        """Get aggregated metrics summary."""
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            queryset = AdminMetricsORM.objects.filter(
                period=period, start_date__gte=start, end_date__lte=end
            )

            if feature_key:
                queryset = queryset.filter(feature_key=feature_key)

            metrics = queryset.order_by("-start_date").first()

            if not metrics:
                # Return empty metrics if no data found
                return Result.success(
                    MetricsSummary(
                        period=period,
                        start_date=start_date,
                        end_date=end_date,
                        feature_key=feature_key,
                        total_cost=0.0,
                        cost_by_feature={},
                        total_tokens=0,
                        tokens_by_feature={},
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_invocations=0,
                        invocations_by_feature={},
                        successful_invocations=0,
                        failed_invocations=0,
                        failure_rate=0.0,
                        failure_reasons={},
                    )
                )

            return Result.success(
                MetricsSummary(
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    feature_key=feature_key,
                    total_cost=float(metrics.total_cost),
                    cost_by_feature=metrics.cost_by_feature,
                    total_tokens=metrics.total_tokens,
                    tokens_by_feature=metrics.tokens_by_feature,
                    prompt_tokens=metrics.prompt_tokens,
                    completion_tokens=metrics.completion_tokens,
                    total_invocations=metrics.total_invocations,
                    invocations_by_feature=metrics.invocations_by_feature,
                    successful_invocations=metrics.successful_invocations,
                    failed_invocations=metrics.failed_invocations,
                    failure_rate=metrics.failure_rate,
                    failure_reasons=metrics.failure_reasons,
                )
            )
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get metrics summary: {str(e)}"),
            )

    async def get_metrics_by_feature(
        self,
        feature_key: str,
        period: str,
        start_date: str,
        end_date: str,
        session: AdminSession,
    ) -> Result[MetricsSummary]:
        """Get metrics for specific feature."""
        return await self.get_metrics_summary(
            period=period,
            start_date=start_date,
            end_date=end_date,
            feature_key=feature_key,
            session=session,
        )


class UserManagementRepository(UserManagementPort):
    """Django ORM implementation of user management port."""

    async def list_users(
        self,
        tenant_id: str | None,
        role: AdminRole | None,
        limit: int,
        offset: int,
        session: AdminSession,
    ) -> Result[list[dict]]:
        """List users with filters."""
        try:
            # Placeholder - would integrate with actual user system
            return Result.success([])
        except Exception as e:
            return Result.failure(DomainError(f"Failed to list users: {str(e)}"),
            )

    async def get_user(self, user_id: UUID, session: AdminSession) -> Result[dict]:
        """Get user details."""
        try:
            # Placeholder - would integrate with actual user system
            return Result.failure(DomainError(f"User {user_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get user: {str(e)}"),
            )

    async def update_user_role(
        self, user_id: UUID, role: AdminRole, session: AdminSession
    ) -> Result[dict]:
        """Update user role."""
        try:
            # Placeholder - would integrate with actual user system
            return Result.failure(DomainError("User role management not implemented"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to update user role: {str(e)}"),
            )

    async def list_tenants(self, session: AdminSession) -> Result[list[dict]]:
        """List all tenants."""
        try:
            tenants = TenantORM.objects.all()
            result = [
                {
                    "id": t.id,
                    "name": t.name,
                    "display_name": t.display_name,
                    "is_active": t.is_active,
                    "plan": t.plan,
                    "max_users": t.max_users,
                    "max_projects": t.max_projects,
                    "max_storage_gb": t.max_storage_gb,
                    "created_at": t.created_at.isoformat(),
                }
                for t in tenants
            ]
            return Result.success(result)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to list tenants: {str(e)}"),
            )

    async def get_tenant(
        self, tenant_id: str, session: AdminSession
    ) -> Result[dict]:
        """Get tenant details."""
        try:
            tenant = TenantORM.objects.get(id=tenant_id)
            return Result.success({
                "id": tenant.id,
                "name": tenant.name,
                "display_name": tenant.display_name,
                "is_active": tenant.is_active,
                "plan": tenant.plan,
                "max_users": tenant.max_users,
                "max_projects": tenant.max_projects,
                "max_storage_gb": tenant.max_storage_gb,
                "created_by": str(tenant.created_by),
                "settings": tenant.settings,
                "created_at": tenant.created_at.isoformat(),
                "updated_at": tenant.updated_at.isoformat(),
            })
        except TenantORM.DoesNotExist:
            return Result.failure(DomainError(f"Tenant {tenant_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get tenant: {str(e)}"),
            )

    async def create_tenant(self, data: dict, session: AdminSession) -> Result[dict]:
        """Create new tenant."""
        try:
            tenant = TenantORM.objects.create(
                id=data["id"],
                name=data["name"],
                display_name=data["display_name"],
                plan=data.get("plan", "free"),
                max_users=data.get("max_users", 5),
                max_projects=data.get("max_projects", 10),
                max_storage_gb=data.get("max_storage_gb", 10),
                created_by=session.user_id,
                settings=data.get("settings", {}),
            )
            return Result.success({
                "id": tenant.id,
                "name": tenant.name,
                "created_at": tenant.created_at.isoformat(),
            })
        except django_models.IntegrityError:
            return Result.failure(DomainError(f"Tenant {data['id']} already exists"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to create tenant: {str(e)}"),
            )

    async def update_tenant(
        self, tenant_id: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update tenant."""
        try:
            tenant = TenantORM.objects.get(id=tenant_id)
            if "name" in data:
                tenant.name = data["name"]
            if "display_name" in data:
                tenant.display_name = data["display_name"]
            if "plan" in data:
                tenant.plan = data["plan"]
            if "max_users" in data:
                tenant.max_users = data["max_users"]
            if "max_projects" in data:
                tenant.max_projects = data["max_projects"]
            if "max_storage_gb" in data:
                tenant.max_storage_gb = data["max_storage_gb"]
            if "settings" in data:
                tenant.settings = data["settings"]
            if "is_active" in data:
                tenant.is_active = data["is_active"]
            tenant.save()
            return Result.success({
                "id": tenant.id,
                "name": tenant.name,
                "updated_at": tenant.updated_at.isoformat(),
            })
        except TenantORM.DoesNotExist:
            return Result.failure(DomainError(f"Tenant {tenant_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to update tenant: {str(e)}"),
            )

    async def deactivate_tenant(
        self, tenant_id: str, session: AdminSession
    ) -> Result[None]:
        """Deactivate tenant."""
        try:
            tenant = TenantORM.objects.get(id=tenant_id)
            tenant.is_active = False
            tenant.save()
            return Result.success(None)
        except TenantORM.DoesNotExist:
            return Result.failure(DomainError(f"Tenant {tenant_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to deactivate tenant: {str(e)}"),
            )


class JobQueueRepository(JobQueuePort):
    """Django ORM implementation of job queue port."""

    async def list_jobs(
        self, filters: JobQueueFilter, session: AdminSession
    ) -> Result[list[dict]]:
        """List jobs with filters."""
        try:
            # Placeholder - would integrate with actual job queue system
            return Result.success([])
        except Exception as e:
            return Result.failure(DomainError(f"Failed to list jobs: {str(e)}"),
            )

    async def get_job(self, job_id: UUID, session: AdminSession) -> Result[dict]:
        """Get job details."""
        try:
            # Placeholder - would integrate with actual job queue system
            return Result.failure(DomainError(f"Job {job_id} not found"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get job: {str(e)}"),
            )

    async def retry_job(self, job_id: UUID, session: AdminSession) -> Result[dict]:
        """Retry failed job."""
        try:
            # Placeholder - would integrate with actual job queue system
            return Result.failure(DomainError("Job retry not implemented"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to retry job: {str(e)}"),
            )

    async def cancel_job(self, job_id: UUID, session: AdminSession) -> Result[None]:
        """Cancel pending or running job."""
        try:
            # Placeholder - would integrate with actual job queue system
            return Result.failure(DomainError("Job cancellation not implemented"))
        except Exception as e:
            return Result.failure(DomainError(f"Failed to cancel job: {str(e)}"),
            )


class PolicyChangeLogRepository(PolicyChangeLogPort):
    """Django ORM implementation of policy change log port."""

    async def log_change(self, entry: PolicyChangeLogEntry) -> Result[None]:
        """Log policy change."""
        try:
            PolicyChangeLogORM.objects.create(
                id=entry.id,
                policy_id=entry.policy_id,
                policy_type=entry.policy_type,
                version=entry.version,
                changed_by=entry.changed_by,
                change_type=entry.change_type,
                previous_version=entry.previous_version,
                change_summary=entry.change_summary,
                change_details=entry.change_details,
            )
            return Result.success(None)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to log change: {str(e)}"),
            )

    async def get_changes(
        self,
        policy_id: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
        session: AdminSession,
    ) -> Result[list[PolicyChangeLogEntry]]:
        """Get policy change log entries."""
        try:
            queryset = PolicyChangeLogORM.objects.all()

            if policy_id:
                queryset = queryset.filter(policy_id=policy_id)
            if start_date:
                start = datetime.fromisoformat(start_date)
                queryset = queryset.filter(created_at__gte=start)
            if end_date:
                end = datetime.fromisoformat(end_date)
                queryset = queryset.filter(created_at__lte=end)

            logs = queryset.order_by("-created_at")[:limit]

            entries = [log.to_domain() for log in logs]
            return Result.success(entries)
        except Exception as e:
            return Result.failure(DomainError(f"Failed to get changes: {str(e)}"),
            )
