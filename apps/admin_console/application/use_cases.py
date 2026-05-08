"""Use cases for admin console application layer.

Orchestrates domain logic and port interactions.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

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
from apps.admin_console.domain.services import (
    AdminPermissionGuard,
    MetricsAggregator,
    PolicyValidator,
)
from apps.admin_console.domain.value_objects import (
    AuditLogFilter,
    FallbackChain,
    JobQueueFilter,
)
from shared.application.result import Result
from shared.domain.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


@dataclass
class DashboardData:
    """Aggregated dashboard data."""

    metrics_summary: MetricsSummary
    recent_policy_changes: list[PolicyChangeLogEntry]
    active_jobs_count: int
    pending_actions_count: int
    system_health: dict[str, Any]


# Use Case: Get Admin Dashboard
class GetAdminDashboard:
    """Get aggregated dashboard data."""

    def __init__(
        self,
        metrics_port: MetricsPort,
        policy_port: PolicyPort,
        policy_log_port: PolicyChangeLogPort,
        job_queue_port: JobQueuePort,
    ) -> None:
        """Initialize use case with ports."""
        self.metrics_port = metrics_port
        self.policy_port = policy_port
        self.policy_log_port = policy_log_port
        self.job_queue_port = job_queue_port

    async def execute(self, session: AdminSession) -> Result[DashboardData]:
        """Execute dashboard data aggregation."""
        try:
            # Permission check
            guard = AdminPermissionGuard(session)
            guard.validate_screen_access("dashboard")

            # Get today's metrics
            today = datetime.now().strftime("%Y-%m-%d")
            metrics_result = await self.metrics_port.get_metrics_summary(
                period="daily",
                start_date=today,
                end_date=today,
                feature_key=None,
                session=session,
            )

            if metrics_result.is_failure:
                return metrics_result

            metrics = metrics_result.value

            # Get recent policy changes
            changes_result = await self.policy_log_port.get_changes(
                policy_id=None,
                start_date=None,
                end_date=None,
                limit=10,
                session=session,
            )

            recent_changes = (
                changes_result.value if changes_result.is_success else []
            )

            # Get active jobs count
            jobs_result = await self.job_queue_port.list_jobs(
                JobQueueFilter(status="running", limit=1),
                session,
            )

            active_jobs = (
                len(jobs_result.value) if jobs_result.is_success else 0
            )

            # Calculate pending actions (policies needing review, etc.)
            pending_result = await self.policy_port.list_feature_policies(session)
            pending_actions = (
                len([p for p in pending_result.value if p.get("needs_review", False)])
                if pending_result.is_success
                else 0
            )

            dashboard_data = DashboardData(
                metrics_summary=metrics,
                recent_policy_changes=recent_changes,
                active_jobs_count=active_jobs,
                pending_actions_count=pending_actions,
                system_health={
                    "status": "healthy",
                    "last_updated": datetime.now().isoformat(),
                },
            )

            return Result.success(dashboard_data)

        except PermissionDeniedError as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(
                ValidationError("dashboard", f"Failed to load dashboard: {str(e)}")
            )


# Use Case: List Users
class ListUsers:
    """List users with optional filters."""

    def __init__(self, user_port: UserManagementPort) -> None:
        """Initialize use case."""
        self.user_port = user_port

    async def execute(
        self,
        session: AdminSession,
        tenant_id: str | None = None,
        role: AdminRole | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[list[dict]]:
        """Execute user list with filters."""
        try:
            guard = AdminPermissionGuard(session)
            guard.validate_screen_access("users")

            if tenant_id:
                guard.validate_tenant_access(tenant_id)

            return await self.user_port.list_users(
                tenant_id, role, limit, offset, session
            )

        except PermissionDeniedError as e:
            return Result.failure(e)


# Use Case: Manage User Role
class ManageUserRole:
    """Update user role and permissions."""

    def __init__(self, user_port: UserManagementPort) -> None:
        """Initialize use case."""
        self.user_port = user_port

    async def execute(
        self,
        user_id: UUID,
        new_role: AdminRole,
        session: AdminSession,
    ) -> Result[dict]:
        """Execute role update."""
        try:
            guard = AdminPermissionGuard(session)
            guard.validate_action("users", "update")

            return await self.user_port.update_user_role(user_id, new_role, session)

        except PermissionDeniedError as e:
            return Result.failure(e)


# Use Case: Get Policy Detail
class GetPolicyDetail:
    """Get policy with version history."""

    def __init__(
        self,
        policy_port: PolicyPort,
        policy_log_port: PolicyChangeLogPort,
    ) -> None:
        """Initialize use case."""
        self.policy_port = policy_port
        self.policy_log_port = policy_log_port

    async def execute(
        self,
        policy_type: str,
        feature_key: str,
        version: int | None,
        session: AdminSession,
    ) -> Result[dict]:
        """Execute policy detail retrieval."""
        try:
            guard = AdminPermissionGuard(session)

            if policy_type == "feature":
                guard.validate_screen_access("policies")
                result = await self.policy_port.get_feature_policy(
                    feature_key, version, session
                )
            elif policy_type == "prompt":
                guard.validate_screen_access("prompt_policies")
                result = await self.policy_port.get_prompt_policy(
                    feature_key, version, session
                )
            else:
                return Result.failure(
                    ValidationError("policy_type", f"Invalid policy type: {policy_type}")
                )

            if result.is_failure:
                return result

            policy_data = result.value

            # Get version history
            history_result = await self.policy_log_port.get_changes(
                feature_key, session
            )

            if history_result.is_success:
                policy_data["version_history"] = [
                    entry.to_dict() for entry in history_result.value
                ]

            return Result.success(policy_data)

        except PermissionDeniedError as e:
            return Result.failure(e)


# Use Case: Edit Policy
class EditPolicy:
    """Validate and create new policy version."""

    def __init__(
        self,
        policy_port: PolicyPort,
        policy_log_port: PolicyChangeLogPort,
    ) -> None:
        """Initialize use case."""
        self.policy_port = policy_port
        self.policy_log_port = policy_log_port
        self.validator = PolicyValidator()

    async def execute(
        self,
        policy_type: str,
        feature_key: str,
        policy_data: dict,
        session: AdminSession,
    ) -> Result[dict]:
        """Execute policy edit."""
        try:
            guard = AdminPermissionGuard(session)

            if policy_type == "feature":
                guard.validate_screen_access("policies")
                guard.validate_action("policies", "update")

                # Validate feature policy
                self.validator.validate_feature_policy(
                    feature_key=feature_key,
                    model_type=policy_data.get("model_type", ""),
                    fallback_chain=FallbackChain(
                        primary_model=policy_data.get("primary_model", ""),
                        fallback_models=policy_data.get("fallback_models", []),
                    ),
                    cost_limit=PolicyValidator,  # type: ignore
                    capabilities=PolicyValidator,  # type: ignore
                )

                result = await self.policy_port.update_feature_policy(
                    feature_key, policy_data, session
                )

            elif policy_type == "prompt":
                guard.validate_screen_access("prompt_policies")
                guard.validate_action("prompt_policies", "update")

                # Validate prompt policy
                self.validator.validate_prompt_policy(
                    feature_key=feature_key,
                    template=PolicyValidator,  # type: ignore
                )

                result = await self.policy_port.update_prompt_policy(
                    feature_key, policy_data, session
                )
            else:
                return Result.failure(
                    ValidationError("policy_type", f"Invalid policy type: {policy_type}")
                )

            return result

        except (PermissionDeniedError, ValidationError) as e:
            return Result.failure(e)


# Use Case: Rollback Policy
class RollbackPolicy:
    """Rollback policy to previous version."""

    def __init__(
        self,
        policy_port: PolicyPort,
        policy_log_port: PolicyChangeLogPort,
    ) -> None:
        """Initialize use case."""
        self.policy_port = policy_port
        self.policy_log_port = policy_log_port

    async def execute(
        self,
        policy_type: str,
        feature_key: str,
        to_version: int,
        reason: str,
        session: AdminSession,
    ) -> Result[dict]:
        """Execute policy rollback."""
        try:
            guard = AdminPermissionGuard(session)

            if policy_type == "feature":
                guard.validate_screen_access("rollback")
                guard.validate_action("policies", "rollback")

                result = await self.policy_port.rollback_feature_policy(
                    feature_key, to_version, reason, session
                )
            elif policy_type == "prompt":
                guard.validate_screen_access("rollback")
                guard.validate_action("prompt_policies", "rollback")

                result = await self.policy_port.rollback_prompt_policy(
                    feature_key, to_version, reason, session
                )
            else:
                return Result.failure(
                    ValidationError("policy_type", f"Invalid policy type: {policy_type}")
                )

            # Log rollback action
            if result.is_success:
                log_entry = PolicyChangeLogEntry(
                    policy_id=feature_key,
                    policy_type=policy_type,  # type: ignore
                    version=result.value.get("version", 0),
                    changed_by=session.user_id,
                    change_type="rollback",
                    previous_version=to_version,
                    change_summary=f"Rollback to version {to_version}: {reason}",
                )
                await self.policy_log_port.log_change(log_entry)

            return result

        except (PermissionDeniedError, ValidationError) as e:
            return Result.failure(e)


# Use Case: Get Metrics
class GetMetrics:
    """Get aggregated metrics by time range."""

    def __init__(self, metrics_port: MetricsPort) -> None:
        """Initialize use case."""
        self.metrics_port = metrics_port

    async def execute(
        self,
        period: str,
        start_date: str,
        end_date: str,
        feature_key: str | None,
        session: AdminSession,
    ) -> Result[MetricsSummary]:
        """Execute metrics retrieval."""
        try:
            guard = AdminPermissionGuard(session)
            guard.validate_screen_access("metrics")

            return await self.metrics_port.get_metrics_summary(
                period, start_date, end_date, feature_key, session
            )

        except PermissionDeniedError as e:
            return Result.failure(e)


# Use Case: Search Audit Logs
class SearchAuditLogs:
    """Search and filter audit logs."""

    def __init__(self, audit_log_port: AuditLogPort) -> None:
        """Initialize use case."""
        self.audit_log_port = audit_log_port

    async def execute(
        self,
        filters: AuditLogFilter,
        session: AdminSession,
    ) -> Result[list[dict]]:
        """Execute audit log search."""
        try:
            guard = AdminPermissionGuard(session)
            guard.validate_screen_access("audit_logs")

            if filters.tenant_id:
                guard.validate_tenant_access(filters.tenant_id)

            return await self.audit_log_port.search_audit_logs(filters, session)

        except PermissionDeniedError as e:
            return Result.failure(e)


# Use Case: Get Job Queue
class GetJobQueue:
    """Get generation job queue status."""

    def __init__(self, job_queue_port: JobQueuePort) -> None:
        """Initialize use case."""
        self.job_queue_port = job_queue_port

    async def execute(
        self,
        filters: JobQueueFilter,
        session: AdminSession,
    ) -> Result[list[dict]]:
        """Execute job queue retrieval."""
        try:
            guard = AdminPermissionGuard(session)
            guard.validate_screen_access("job_queue")

            if filters.tenant_id:
                guard.validate_tenant_access(filters.tenant_id)

            return await self.job_queue_port.list_jobs(filters, session)

        except PermissionDeniedError as e:
            return Result.failure(e)
