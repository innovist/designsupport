"""Application ports for admin console.

Interfaces for external dependencies following Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

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
from shared.application.result import Result


# Model Catalog Port
class ModelCatalogPort(ABC):
    """Port for accessing model catalog data."""

    @abstractmethod
    async def list_providers(self, session: AdminSession) -> Result[list[dict]]:
        """List all model providers."""
        pass

    @abstractmethod
    async def get_provider(self, provider_id: str, session: AdminSession) -> Result[dict]:
        """Get provider details."""
        pass

    @abstractmethod
    async def create_provider(self, data: dict, session: AdminSession) -> Result[dict]:
        """Create new provider."""
        pass

    @abstractmethod
    async def update_provider(
        self, provider_id: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update provider."""
        pass

    @abstractmethod
    async def deactivate_provider(
        self, provider_id: str, session: AdminSession
    ) -> Result[None]:
        """Deactivate provider."""
        pass

    @abstractmethod
    async def list_models(self, session: AdminSession) -> Result[list[dict]]:
        """List all models."""
        pass

    @abstractmethod
    async def get_model(self, model_id: str, session: AdminSession) -> Result[dict]:
        """Get model details."""
        pass

    @abstractmethod
    async def create_model(self, data: dict, session: AdminSession) -> Result[dict]:
        """Create new model."""
        pass

    @abstractmethod
    async def update_model(
        self, model_id: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update model."""
        pass

    @abstractmethod
    async def deactivate_model(self, model_id: str, session: AdminSession) -> Result[None]:
        """Deactivate model."""
        pass


# Policy Port
class PolicyPort(ABC):
    """Port for accessing policy data."""

    @abstractmethod
    async def list_feature_policies(self, session: AdminSession) -> Result[list[dict]]:
        """List all feature policies."""
        pass

    @abstractmethod
    async def get_feature_policy(
        self, feature_key: str, version: int | None, session: AdminSession
    ) -> Result[dict]:
        """Get feature policy with version history."""
        pass

    @abstractmethod
    async def create_feature_policy(
        self, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Create new feature policy."""
        pass

    @abstractmethod
    async def update_feature_policy(
        self, feature_key: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update feature policy (creates new version)."""
        pass

    @abstractmethod
    async def rollback_feature_policy(
        self,
        feature_key: str,
        to_version: int,
        reason: str,
        session: AdminSession,
    ) -> Result[dict]:
        """Rollback feature policy to previous version."""
        pass

    @abstractmethod
    async def list_prompt_policies(self, session: AdminSession) -> Result[list[dict]]:
        """List all prompt policies."""
        pass

    @abstractmethod
    async def get_prompt_policy(
        self, feature_key: str, version: int | None, session: AdminSession
    ) -> Result[dict]:
        """Get prompt policy with version history."""
        pass

    @abstractmethod
    async def update_prompt_policy(
        self, feature_key: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update prompt policy (creates new version)."""
        pass

    @abstractmethod
    async def rollback_prompt_policy(
        self,
        feature_key: str,
        to_version: int,
        reason: str,
        session: AdminSession,
    ) -> Result[dict]:
        """Rollback prompt policy to previous version."""
        pass

    @abstractmethod
    async def get_policy_history(
        self, policy_id: str, session: AdminSession
    ) -> Result[list[PolicyChangeLogEntry]]:
        """Get policy version history."""
        pass


# Audit Log Port
class AuditLogPort(ABC):
    """Port for accessing audit logs."""

    @abstractmethod
    async def search_audit_logs(
        self, filters: AuditLogFilter, session: AdminSession
    ) -> Result[list[dict]]:
        """Search audit logs with filters."""
        pass

    @abstractmethod
    async def get_audit_log_detail(self, log_id: UUID, session: AdminSession) -> Result[dict]:
        """Get audit log detail."""
        pass


# Metrics Port
class MetricsPort(ABC):
    """Port for accessing metrics data."""

    @abstractmethod
    async def get_metrics_summary(
        self,
        period: str,
        start_date: str,
        end_date: str,
        feature_key: str | None,
        session: AdminSession,
    ) -> Result[MetricsSummary]:
        """Get aggregated metrics summary."""
        pass

    @abstractmethod
    async def get_metrics_by_feature(
        self,
        feature_key: str,
        period: str,
        start_date: str,
        end_date: str,
        session: AdminSession,
    ) -> Result[MetricsSummary]:
        """Get metrics for specific feature."""
        pass


# User Management Port
class UserManagementPort(ABC):
    """Port for user and tenant management."""

    @abstractmethod
    async def list_users(
        self,
        tenant_id: str | None,
        role: AdminRole | None,
        limit: int,
        offset: int,
        session: AdminSession,
    ) -> Result[list[dict]]:
        """List users with filters."""
        pass

    @abstractmethod
    async def get_user(self, user_id: UUID, session: AdminSession) -> Result[dict]:
        """Get user details."""
        pass

    @abstractmethod
    async def update_user_role(
        self, user_id: UUID, role: AdminRole, session: AdminSession
    ) -> Result[dict]:
        """Update user role."""
        pass

    @abstractmethod
    async def list_tenants(self, session: AdminSession) -> Result[list[dict]]:
        """List all tenants."""
        pass

    @abstractmethod
    async def get_tenant(self, tenant_id: str, session: AdminSession) -> Result[dict]:
        """Get tenant details."""
        pass

    @abstractmethod
    async def create_tenant(self, data: dict, session: AdminSession) -> Result[dict]:
        """Create new tenant."""
        pass

    @abstractmethod
    async def update_tenant(
        self, tenant_id: str, data: dict, session: AdminSession
    ) -> Result[dict]:
        """Update tenant."""
        pass

    @abstractmethod
    async def deactivate_tenant(self, tenant_id: str, session: AdminSession) -> Result[None]:
        """Deactivate tenant."""
        pass


# Job Queue Port
class JobQueuePort(ABC):
    """Port for accessing generation job queue."""

    @abstractmethod
    async def list_jobs(
        self, filters: JobQueueFilter, session: AdminSession
    ) -> Result[list[dict]]:
        """List jobs with filters."""
        pass

    @abstractmethod
    async def get_job(self, job_id: UUID, session: AdminSession) -> Result[dict]:
        """Get job details."""
        pass

    @abstractmethod
    async def retry_job(self, job_id: UUID, session: AdminSession) -> Result[dict]:
        """Retry failed job."""
        pass

    @abstractmethod
    async def cancel_job(self, job_id: UUID, session: AdminSession) -> Result[None]:
        """Cancel pending or running job."""
        pass


# Policy Change Log Port
class PolicyChangeLogPort(ABC):
    """Port for logging policy changes."""

    @abstractmethod
    async def log_change(self, entry: PolicyChangeLogEntry) -> Result[None]:
        """Log policy change."""
        pass

    @abstractmethod
    async def get_changes(
        self,
        policy_id: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
        session: AdminSession,
    ) -> Result[list[PolicyChangeLogEntry]]:
        """Get policy change log entries."""
        pass
