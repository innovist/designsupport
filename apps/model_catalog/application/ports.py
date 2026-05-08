"""Repository ports for model catalog.

Defines abstract interfaces for repositories (Dependency Inversion).
"""
from abc import ABC, abstractmethod
from typing import Any

from apps.model_catalog.domain.entities import (
    FeatureModelPolicy,
    ModelCatalog,
    ModelInvocation,
    ModelProvider,
    ModelType,
    PolicyChangeLog,
    PromptPolicy,
)


class ModelProviderRepositoryPort(ABC):
    """Repository port for ModelProvider entities."""

    @abstractmethod
    async def create(self, provider: ModelProvider) -> ModelProvider:
        """Create a new provider."""
        pass

    @abstractmethod
    async def get_by_id(self, provider_id: str) -> ModelProvider | None:
        """Get provider by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> ModelProvider | None:
        """Get provider by name."""
        pass

    @abstractmethod
    async def list_all(self, active_only: bool = False) -> list[ModelProvider]:
        """List all providers."""
        pass

    @abstractmethod
    async def update(self, provider_id: str, **kwargs) -> ModelProvider | None:
        """Update provider fields."""
        pass

    @abstractmethod
    async def deactivate(self, provider_id: str) -> bool:
        """Deactivate a provider."""
        pass


class ModelCatalogRepositoryPort(ABC):
    """Repository port for ModelCatalog entities."""

    @abstractmethod
    async def create(self, model: ModelCatalog) -> ModelCatalog:
        """Create a new model catalog entry."""
        pass

    @abstractmethod
    async def get_by_id(self, model_id: str) -> ModelCatalog | None:
        """Get model by ID."""
        pass

    @abstractmethod
    async def get_provider_by_id(self, provider_id: str) -> ModelProvider | None:
        """Get provider by ID."""
        pass

    @abstractmethod
    async def get_by_provider(self, provider_id: str) -> list[ModelCatalog]:
        """Get all models for a provider."""
        pass

    @abstractmethod
    async def list_by_type(
        self,
        model_type: ModelType,
        active_only: bool = False,
    ) -> list[ModelCatalog]:
        """List models by type."""
        pass

    @abstractmethod
    async def list_all(
        self,
        provider_id: str | None = None,
        model_type: ModelType | None = None,
        active_only: bool = False,
    ) -> list[ModelCatalog]:
        """List models with optional filters."""
        pass

    @abstractmethod
    async def update(self, model_id: str, **kwargs) -> ModelCatalog | None:
        """Update model fields."""
        pass

    @abstractmethod
    async def deactivate(self, model_id: str) -> bool:
        """Deactivate a model."""
        pass


class FeatureModelPolicyRepositoryPort(ABC):
    """Repository port for FeatureModelPolicy entities."""

    @abstractmethod
    async def create(self, policy: FeatureModelPolicy) -> FeatureModelPolicy:
        """Create a new feature policy."""
        pass

    @abstractmethod
    async def get_by_id(self, policy_id: str) -> FeatureModelPolicy | None:
        """Get policy by ID."""
        pass

    @abstractmethod
    async def get_active_by_feature(self, feature_key: str) -> FeatureModelPolicy | None:
        """Get active policy for a feature."""
        pass

    @abstractmethod
    async def list_by_feature(self, feature_key: str) -> list[FeatureModelPolicy]:
        """List all policies for a feature (all versions)."""
        pass

    @abstractmethod
    async def list_all(self, active_only: bool = False) -> list[FeatureModelPolicy]:
        """List all policies."""
        pass

    @abstractmethod
    async def get_version(self, policy_id: str, version: int) -> FeatureModelPolicy | None:
        """Get specific version of a policy."""
        pass

    @abstractmethod
    async def deactivate(self, policy_id: str) -> bool:
        """Deactivate a policy."""
        pass


class PromptPolicyRepositoryPort(ABC):
    """Repository port for PromptPolicy entities."""

    @abstractmethod
    async def create(self, policy: PromptPolicy) -> PromptPolicy:
        """Create a new prompt policy."""
        pass

    @abstractmethod
    async def get_by_id(self, policy_id: str) -> PromptPolicy | None:
        """Get prompt policy by ID."""
        pass

    @abstractmethod
    async def get_active_by_feature(self, feature_key: str) -> PromptPolicy | None:
        """Get active prompt policy for a feature."""
        pass

    @abstractmethod
    async def list_by_feature(self, feature_key: str) -> list[PromptPolicy]:
        """List all prompt policies for a feature."""
        pass

    @abstractmethod
    async def list_all(self, active_only: bool = False) -> list[PromptPolicy]:
        """List all prompt policies."""
        pass

    @abstractmethod
    async def get_version(self, policy_id: str, version: int) -> PromptPolicy | None:
        """Get specific version of a prompt policy."""
        pass

    @abstractmethod
    async def deactivate(self, policy_id: str) -> bool:
        """Deactivate a prompt policy."""
        pass


class ModelInvocationRepositoryPort(ABC):
    """Repository port for ModelInvocation entities."""

    @abstractmethod
    async def create(self, invocation: ModelInvocation) -> ModelInvocation:
        """Create a new invocation record."""
        pass

    @abstractmethod
    async def get_by_id(self, invocation_id: str) -> ModelInvocation | None:
        """Get invocation by ID."""
        pass

    @abstractmethod
    async def list_by_feature(
        self,
        feature_key: str,
        start_time: Any | None = None,
        end_time: Any | None = None,
    ) -> list[ModelInvocation]:
        """List invocations for a feature."""
        pass

    @abstractmethod
    async def list_by_session(self, session_id: str) -> list[ModelInvocation]:
        """List invocations for a session."""
        pass

    @abstractmethod
    async def aggregate_metrics(
        self,
        feature_key: str,
        start_time: Any | None = None,
        end_time: Any | None = None,
    ) -> dict[str, Any]:
        """Aggregate metrics by feature and time range."""
        pass


class PolicyChangeLogRepositoryPort(ABC):
    """Repository port for PolicyChangeLog entities."""

    @abstractmethod
    async def create(self, change_log: PolicyChangeLog) -> PolicyChangeLog:
        """Create a new change log entry."""
        pass

    @abstractmethod
    async def list_by_target(
        self,
        target_type: str,
        target_id: str,
    ) -> list[PolicyChangeLog]:
        """List change logs for a specific policy."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100) -> list[PolicyChangeLog]:
        """List recent change logs."""
        pass


class ProviderAdapterPort(ABC):
    """Adapter port for calling external provider APIs."""

    @abstractmethod
    async def call_model(
        self,
        provider: ModelProvider,
        model: ModelCatalog,
        payload: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a model via provider API.

        Args:
            provider: Provider configuration
            model: Model to call
            payload: Request payload
            options: Additional options

        Returns:
            Response dictionary with usage metrics

        Raises:
            OperationError: If API call fails
        """
        pass
