"""Django ORM models for model catalog.

Implements persistence layer using Django ORM.
"""
import os
import uuid
from datetime import datetime

from django.db import models

from shared.infrastructure.orm.base_model import TimestampedModel

from apps.model_catalog.domain.entities import (
    AuthScheme,
    InvocationStatus,
    ModelType,
)


def _utcnow() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now()


class ModelProviderModel(TimestampedModel):
    """Django ORM model for ModelProvider entity.

    Implements REQ-04-CATALOG-001: Provider configuration.
    """

    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    api_key_env = models.CharField(max_length=255)
    base_url = models.URLField(max_length=500, null=True, blank=True)
    endpoint_path = models.CharField(max_length=255, null=True, blank=True)
    auth_scheme = models.CharField(
        max_length=50,
        choices=[(scheme.value, scheme.name) for scheme in AuthScheme],
        default=AuthScheme.BEARER.value,
    )
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "model_providers"
        verbose_name = "Model Provider"
        verbose_name_plural = "Model Providers"
        indexes = [
            models.Index(fields=["name", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    def to_domain(self):
        """Convert to domain entity."""
        from apps.model_catalog.domain.entities import ModelProvider

        return ModelProvider(
            id=self.id,
            name=self.name,
            api_key_env=self.api_key_env,
            base_url=self.base_url,
            endpoint_path=self.endpoint_path,
            auth_scheme=AuthScheme(self.auth_scheme),  # type: ignore
            active=self.active,
        )

    @classmethod
    def from_domain(cls, provider):
        """Create from domain entity."""
        return cls(
            id=provider.id,
            name=provider.name,
            api_key_env=provider.api_key_env,
            base_url=provider.base_url,
            endpoint_path=provider.endpoint_path,
            auth_scheme=provider.auth_scheme.value,
            active=provider.active,
        )


class ModelCatalogModel(TimestampedModel):
    """Django ORM model for ModelCatalog entity.

    Implements REQ-04-CATALOG-002: Model catalog entries.
    """

    id = models.CharField(max_length=255, primary_key=True)
    provider = models.ForeignKey(
        ModelProviderModel,
        on_delete=models.PROTECT,
        related_name="models",
        db_index=True,
    )
    model_name = models.CharField(max_length=255, db_index=True)
    type = models.CharField(
        max_length=50,
        choices=[(mt.value, mt.name) for mt in ModelType],
        db_index=True,
    )
    context_limit = models.IntegerField(null=True, blank=True)
    cost_estimate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )
    modalities = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "model_catalog"
        verbose_name = "Model Catalog Entry"
        verbose_name_plural = "Model Catalog Entries"
        unique_together = [["provider", "model_name"]]
        indexes = [
            models.Index(fields=["provider", "active"]),
            models.Index(fields=["type", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.provider.name}/{self.model_name} ({self.type})"

    def to_domain(self):
        """Convert to domain entity."""
        from apps.model_catalog.domain.entities import ModelCatalog

        return ModelCatalog(
            id=self.id,
            provider_id=self.provider_id,
            model_name=self.model_name,
            type=ModelType(self.type),  # type: ignore
            context_limit=self.context_limit,
            cost_estimate=float(self.cost_estimate) if self.cost_estimate else None,
            modalities=self.modalities or [],
            active=self.active,
        )

    @classmethod
    def from_domain(cls, model):
        """Create from domain entity."""
        return cls(
            id=model.id,
            provider_id=model.provider_id,
            model_name=model.model_name,
            type=model.type.value,
            context_limit=model.context_limit,
            cost_estimate=model.cost_estimate,
            modalities=model.modalities,
            active=model.active,
        )


class FeatureModelPolicyModel(TimestampedModel):
    """Django ORM model for FeatureModelPolicy entity.

    Implements REQ-04-POLICY-002: Feature-to-model mapping.
    """

    id = models.CharField(max_length=255, primary_key=True)
    feature_key = models.CharField(max_length=255, unique=True, db_index=True)
    primary_model = models.ForeignKey(
        ModelCatalogModel,
        on_delete=models.PROTECT,
        related_name="primary_policies",
        db_index=True,
    )
    fallback_models = models.ManyToManyField(
        ModelCatalogModel,
        related_name="fallback_policies",
        blank=True,
    )
    parameters = models.JSONField(default=dict, blank=True)
    max_cost_per_call = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )
    max_tokens = models.IntegerField(null=True, blank=True)
    version = models.IntegerField(default=1)
    active = models.BooleanField(default=True, db_index=True)
    reviewer = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "feature_model_policies"
        verbose_name = "Feature Model Policy"
        verbose_name_plural = "Feature Model Policies"
        indexes = [
            models.Index(fields=["feature_key", "active"]),
            models.Index(fields=["version"]),
        ]

    def __str__(self) -> str:
        return f"{self.feature_key} v{self.version} → {self.primary_model.model_name}"

    def to_domain(self):
        """Convert to domain entity."""
        from apps.model_catalog.domain.entities import FeatureModelPolicy

        return FeatureModelPolicy(
            id=self.id,
            feature_key=self.feature_key,
            primary_model_id=self.primary_model_id,
            fallback_model_ids=list(
                self.fallback_models.values_list("id", flat=True)
            ),
            parameters=self.parameters or {},
            max_cost_per_call=float(self.max_cost_per_call) if self.max_cost_per_call else None,
            max_tokens=self.max_tokens,
            version=self.version,
            active=self.active,
            reviewer=self.reviewer,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, policy):
        """Create from domain entity."""
        instance = cls(
            id=policy.id,
            feature_key=policy.feature_key,
            primary_model_id=policy.primary_model_id,
            parameters=policy.parameters,
            max_cost_per_call=policy.max_cost_per_call,
            max_tokens=policy.max_tokens,
            version=policy.version,
            active=policy.active,
            reviewer=policy.reviewer,
            created_at=policy.created_at,
        )
        return instance


class PromptPolicyModel(TimestampedModel):
    """Django ORM model for PromptPolicy entity.

    Implements REQ-04-POLICY-003: Prompt template policies.
    """

    id = models.CharField(max_length=255, primary_key=True)
    feature_key = models.CharField(max_length=255, db_index=True)
    prompt_version = models.CharField(max_length=255)
    system_prompt = models.TextField()
    user_template = models.TextField()
    active = models.BooleanField(default=True, db_index=True)
    reviewer = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "prompt_policies"
        verbose_name = "Prompt Policy"
        verbose_name_plural = "Prompt Policies"
        unique_together = [["feature_key", "prompt_version"]]
        indexes = [
            models.Index(fields=["feature_key", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.feature_key} → {self.prompt_version}"

    def to_domain(self):
        """Convert to domain entity."""
        from apps.model_catalog.domain.entities import PromptPolicy

        return PromptPolicy(
            id=self.id,
            feature_key=self.feature_key,
            prompt_version=self.prompt_version,
            system_prompt=self.system_prompt,
            user_template=self.user_template,
            active=self.active,
            reviewer=self.reviewer,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, policy):
        """Create from domain entity."""
        return cls(
            id=policy.id,
            feature_key=policy.feature_key,
            prompt_version=policy.prompt_version,
            system_prompt=policy.system_prompt,
            user_template=policy.user_template,
            active=policy.active,
            reviewer=policy.reviewer,
            created_at=policy.created_at,
        )


class ModelInvocationModel(TimestampedModel):
    """Django ORM model for ModelInvocation entity.

    Implements REQ-04-ROUTER-004: Invocation metrics collection.
    """

    id = models.CharField(max_length=255, primary_key=True)
    feature_key = models.CharField(max_length=255, db_index=True)
    tenant_id = models.CharField(max_length=255, db_index=True)
    workspace_id = models.UUIDField(db_index=True)
    session_id = models.UUIDField(null=True, blank=True, db_index=True)
    model = models.ForeignKey(
        ModelCatalogModel,
        on_delete=models.PROTECT,
        related_name="invocations",
        db_index=True,
    )
    status = models.CharField(
        max_length=50,
        choices=[(status.value, status.name) for status in InvocationStatus],
        db_index=True,
    )
    tokens_in = models.IntegerField(null=True, blank=True)
    tokens_out = models.IntegerField(null=True, blank=True)
    cost_estimate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )
    latency_ms = models.IntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=255, null=True, blank=True)
    error_summary = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "model_invocations"
        verbose_name = "Model Invocation"
        verbose_name_plural = "Model Invocations"
        indexes = [
            models.Index(fields=["feature_key", "-created_at"]),
            models.Index(fields=["tenant_id", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.feature_key} → {self.model.model_name} ({self.status})"

    def to_domain(self):
        """Convert to domain entity."""
        from apps.model_catalog.domain.entities import ModelInvocation

        return ModelInvocation(
            id=self.id,
            feature_key=self.feature_key,
            tenant_id=self.tenant_id,
            workspace_id=str(self.workspace_id),
            session_id=str(self.session_id) if self.session_id else None,
            model_id=self.model_id,
            status=InvocationStatus(self.status),  # type: ignore
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            cost_estimate=float(self.cost_estimate) if self.cost_estimate else None,
            latency_ms=self.latency_ms,
            error_code=self.error_code,
            error_summary=self.error_summary,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, invocation):
        """Create from domain entity."""
        return cls(
            id=invocation.id,
            feature_key=invocation.feature_key,
            tenant_id=invocation.tenant_id,
            workspace_id=invocation.workspace_id,
            session_id=invocation.session_id,
            model_id=invocation.model_id,
            status=invocation.status.value,
            tokens_in=invocation.tokens_in,
            tokens_out=invocation.tokens_out,
            cost_estimate=invocation.cost_estimate,
            latency_ms=invocation.latency_ms,
            error_code=invocation.error_code,
            error_summary=invocation.error_summary,
            created_at=invocation.created_at,
        )


class PolicyChangeLogModel(TimestampedModel):
    """Django ORM model for PolicyChangeLog entity.

    Implements REQ-04-POLICY-005: Policy change tracking.
    """

    id = models.CharField(max_length=255, primary_key=True)
    target_type = models.CharField(max_length=255, db_index=True)
    target_id = models.CharField(max_length=255, db_index=True)
    version_from = models.IntegerField(null=True, blank=True)
    version_to = models.IntegerField()
    actor_id = models.CharField(max_length=255)
    reason = models.TextField()

    class Meta:
        db_table = "policy_change_logs"
        verbose_name = "Policy Change Log"
        verbose_name_plural = "Policy Change Logs"
        indexes = [
            models.Index(fields=["target_type", "target_id", "-created_at"]),
            models.Index(fields=["actor_id", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.target_type}:{self.target_id} v{self.version_from}→v{self.version_to}"

    def to_domain(self):
        """Convert to domain entity."""
        from apps.model_catalog.domain.entities import PolicyChangeLog

        return PolicyChangeLog(
            id=self.id,
            target_type=self.target_type,
            target_id=self.target_id,
            version_from=self.version_from,
            version_to=self.version_to,
            actor_id=self.actor_id,
            reason=self.reason,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, change_log):
        """Create from domain entity."""
        return cls(
            id=change_log.id,
            target_type=change_log.target_type,
            target_id=change_log.target_id,
            version_from=change_log.version_from,
            version_to=change_log.version_to,
            actor_id=change_log.actor_id,
            reason=change_log.reason,
            created_at=change_log.created_at,
        )
