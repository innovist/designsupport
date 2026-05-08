"""Domain services for admin console.

Pure Python business logic with no Django dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from apps.admin_console.domain.entities import (
    AdminRole,
    AdminSession,
    MetricsSummary,
)
from apps.admin_console.domain.value_objects import (
    CostLimit,
    FallbackChain,
    ModelCapabilities,
    PromptTemplate,
)
from shared.domain.exceptions import (
    PermissionDeniedError,
    ValidationError,
)


# @MX:ANCHOR: [Permission matrix for role-based access control]
# @MX:REASON: Core security contract enforcing role-based screen access across admin console
class PermissionMatrix:
    """Role-based permission matrix for admin actions."""

    # Screen access by role
    SCREEN_PERMISSIONS: dict[str, set[AdminRole]] = {
        "dashboard": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN, AdminRole.VIEWER},
        "providers": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN},
        "models": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN, AdminRole.VIEWER},
        "policies": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN},
        "prompt_policies": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN},
        "metrics": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN, AdminRole.VIEWER},
        "audit_logs": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN, AdminRole.VIEWER},
        "rollback": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN},
        "job_queue": {AdminRole.SUPER_ADMIN, AdminRole.TENANT_ADMIN, AdminRole.VIEWER},
        "users": {AdminRole.SUPER_ADMIN},
        "tenants": {AdminRole.SUPER_ADMIN},
    }

    # Action permissions by role
    ACTION_PERMISSIONS: dict[AdminRole, set[str]] = {
        AdminRole.SUPER_ADMIN: {
            "create", "read", "update", "delete", "rollback", "impersonate"
        },
        AdminRole.TENANT_ADMIN: {
            "create", "read", "update", "delete", "rollback"
        },
        AdminRole.VIEWER: {"read"},
    }

    @classmethod
    def can_access_screen(cls, screen_id: str, role: AdminRole) -> bool:
        """Check if role can access screen."""
        allowed_roles = cls.SCREEN_PERMISSIONS.get(screen_id, set())
        return role in allowed_roles

    @classmethod
    def can_perform_action(cls, role: AdminRole, action: str) -> bool:
        """Check if role can perform action."""
        allowed_actions = cls.ACTION_PERMISSIONS.get(role, set())
        return action in allowed_actions

    @classmethod
    def get_accessible_screens(cls, role: AdminRole) -> list[str]:
        """Get list of screens accessible to role."""
        return [
            screen_id
            for screen_id, allowed_roles in cls.SCREEN_PERMISSIONS.items()
            if role in allowed_roles
        ]


# @MX:ANCHOR: [Admin permission validation service]
# @MX:REASON: Centralized security validation for all admin operations
class AdminPermissionGuard:
    """Guards admin operations with permission checks."""

    def __init__(self, session: AdminSession) -> None:
        """Initialize guard with admin session."""
        self.session = session

    def validate_screen_access(self, screen_id: str) -> None:
        """Validate access to admin screen."""
        if not self.session.is_active:
            raise PermissionDeniedError(
                "access_screen", f"Session {self.session.id} is inactive"
            )

        if self.session.is_expired():
            raise PermissionDeniedError(
                "access_screen", f"Session {self.session.id} is expired"
            )

        if not PermissionMatrix.can_access_screen(screen_id, self.session.role):
            raise PermissionDeniedError(
                f"access_{screen_id}",
                f"Role {self.session.role} cannot access {screen_id}"
            )

    def validate_action(self, resource: str, action: str) -> None:
        """Validate permission for resource action."""
        if not self.session.is_active:
            raise PermissionDeniedError(
                f"{action}_{resource}", f"Session {self.session.id} is inactive"
            )

        if not PermissionMatrix.can_perform_action(self.session.role, action):
            raise PermissionDeniedError(
                f"{action}_{resource}",
                f"Role {self.session.role} cannot perform {action} on {resource}"
            )

        if not self.session.has_permission(resource, action):
            raise PermissionDeniedError(
                f"{action}_{resource}",
                f"Session lacks explicit permission for {action} on {resource}"
            )

    def validate_tenant_access(self, tenant_id: str) -> None:
        """Validate tenant access (tenant isolation)."""
        if self.session.role == AdminRole.SUPER_ADMIN:
            return

        if self.session.tenant_id != tenant_id:
            raise PermissionDeniedError(
                "access_tenant",
                f"Session tenant {self.session.tenant_id} cannot access {tenant_id}"
            )


# @MX:ANCHOR: [Policy validation service]
# @MX:REASON: Ensures policy changes maintain domain invariants before persistence
class PolicyValidator:
    """Validates policy changes before persistence."""

    def validate_feature_policy(
        self,
        feature_key: str,
        model_type: str,
        fallback_chain: FallbackChain,
        cost_limit: CostLimit,
        capabilities: ModelCapabilities,
    ) -> None:
        """Validate feature policy configuration."""
        # Validate feature key exists
        valid_keys = [
            "trend_analysis", "design_generation", "comment_insight",
            "report_generation", "image_search", "recommendation",
            "style_transfer", "virtual_tryon", "size_prediction"
        ]
        if feature_key not in valid_keys:
            raise ValidationError(
                "feature_key",
                f"Invalid feature key: {feature_key}. Must be one of {valid_keys}"
            )

        # Validate model type matches capabilities
        if model_type not in [t.value for t in capabilities.required_types]:
            raise ValidationError(
                "model_type",
                f"Model type {model_type} not in required capabilities {capabilities.required_types}"
            )

        # Validate fallback chain is not empty
        if not fallback_chain.get_full_chain():
            raise ValidationError(
                "fallback_chain",
                "Fallback chain cannot be empty"
            )

        # Validate cost limits are reasonable
        if cost_limit.max_cost_per_request > 100.0:
            raise ValidationError(
                "max_cost_per_request",
                "Max cost per request cannot exceed $100"
            )

        if cost_limit.max_cost_per_day > 10000.0:
            raise ValidationError(
                "max_cost_per_day",
                "Max daily cost cannot exceed $10,000"
            )

    def validate_prompt_policy(
        self,
        feature_key: str,
        template: PromptTemplate,
    ) -> None:
        """Validate prompt policy configuration."""
        # Validate feature key
        valid_keys = [
            "trend_analysis", "design_generation", "comment_insight",
            "report_generation", "image_search", "recommendation",
            "style_transfer", "virtual_tryon", "size_prediction"
        ]
        if feature_key not in valid_keys:
            raise ValidationError(
                "feature_key",
                f"Invalid feature key: {feature_key}"
            )

        # Validate prompt template content
        if len(template.system_prompt) > 10000:
            raise ValidationError(
                "system_prompt",
                "System prompt cannot exceed 10,000 characters"
            )

        if len(template.user_template) > 10000:
            raise ValidationError(
                "user_template",
                "User template cannot exceed 10,000 characters"
            )

        # Validate placeholder variables in template
        if "{user_input}" not in template.user_template:
            raise ValidationError(
                "user_template",
                "User template must contain {{user_input}} placeholder"
            )


# @MX:NOTE: [Metrics aggregation service]
# @MX:REASON: Demoted from ANCHOR (per-file limit 3); only called by admin dashboard view
class MetricsAggregator:
    """Aggregates metrics from model invocations."""

    def __init__(self) -> None:
        """Initialize aggregator."""
        self.reset()

    def reset(self) -> None:
        """Reset aggregation state."""
        self._invocations: list[dict] = []

    def add_invocation(self, invocation: dict[str, Any]) -> None:
        """Add invocation data for aggregation."""
        self._invocations.append(invocation)

    def aggregate_daily(self, date: datetime) -> MetricsSummary:
        """Aggregate metrics for a single day."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        daily_invocations = [
            inv for inv in self._invocations
            if start_of_day <= datetime.fromisoformat(inv["timestamp"]) < end_of_day
        ]

        return self._aggregate(
            daily_invocations,
            period="daily",
            start_date=start_of_day,
            end_date=end_of_day,
        )

    def aggregate_weekly(self, date: datetime) -> MetricsSummary:
        """Aggregate metrics for a week."""
        start_of_week = date - timedelta(days=date.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(weeks=1)

        weekly_invocations = [
            inv for inv in self._invocations
            if start_of_week <= datetime.fromisoformat(inv["timestamp"]) < end_of_week
        ]

        return self._aggregate(
            weekly_invocations,
            period="weekly",
            start_date=start_of_week,
            end_date=end_of_week,
        )

    def aggregate_monthly(self, date: datetime) -> MetricsSummary:
        """Aggregate metrics for a month."""
        start_of_month = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if date.month == 12:
            end_of_month = start_of_month.replace(year=date.year + 1, month=1)
        else:
            end_of_month = start_of_month.replace(month=date.month + 1)

        monthly_invocations = [
            inv for inv in self._invocations
            if start_of_month <= datetime.fromisoformat(inv["timestamp"]) < end_of_month
        ]

        return self._aggregate(
            monthly_invocations,
            period="monthly",
            start_date=start_of_month,
            end_date=end_of_month,
        )

    def _aggregate(
        self,
        invocations: list[dict[str, Any]],
        period: str,
        start_date: datetime,
        end_date: datetime,
    ) -> MetricsSummary:
        """Perform aggregation on filtered invocations."""
        summary = MetricsSummary(
            period=period,  # type: ignore
            start_date=start_date,
            end_date=end_date,
        )

        for inv in invocations:
            # Cost metrics
            cost = inv.get("cost", 0.0)
            summary.total_cost += cost
            feature = inv.get("feature_key", "unknown")
            summary.cost_by_feature[feature] = summary.cost_by_feature.get(feature, 0.0) + cost

            # Token metrics
            prompt_tokens = inv.get("prompt_tokens", 0)
            completion_tokens = inv.get("completion_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens

            summary.total_tokens += total_tokens
            summary.prompt_tokens += prompt_tokens
            summary.completion_tokens += completion_tokens
            summary.tokens_by_feature[feature] = summary.tokens_by_feature.get(feature, 0) + total_tokens

            # Invocation metrics
            summary.total_invocations += 1
            summary.invocations_by_feature[feature] = summary.invocations_by_feature.get(feature, 0) + 1

            # Success/failure
            if inv.get("status") == "success":
                summary.successful_invocations += 1
            else:
                summary.failed_invocations += 1
                failure_reason = inv.get("error", "unknown")
                summary.failure_reasons[failure_reason] = summary.failure_reasons.get(failure_reason, 0) + 1

        summary.calculate_failure_rate()
        return summary


@dataclass
class PolicyDiff:
    """Diff between two policy versions."""

    version_from: int
    version_to: int
    changes: dict[str, tuple[Any, Any]] = field(default_factory=dict)

    def add_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Add a field change."""
        self.changes[field] = (old_value, new_value)

    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.changes) > 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "version_from": self.version_from,
            "version_to": self.version_to,
            "changes": {
                field: {"old": old, "new": new}
                for field, (old, new) in self.changes.items()
            },
        }
