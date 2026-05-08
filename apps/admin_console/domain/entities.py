"""Domain entities for admin console.

Pure Python domain entities with no Django dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4


class AdminRole(str, Enum):
    """Admin role types with hierarchical permissions."""

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    VIEWER = "viewer"


@dataclass(frozen=True)
class AdminPermission:
    """Permission grant for a specific admin action."""

    resource: str  # e.g., "models", "policies", "users"
    action: str  # e.g., "create", "read", "update", "delete", "rollback"
    scope: Literal["all", "tenant", "own"] = "all"

    def matches(self, required_resource: str, required_action: str) -> bool:
        """Check if permission matches required resource and action."""
        return (
            self.resource == required_resource
            and self.action == required_action
        )


@dataclass(frozen=True)
class ScreenPermission:
    """Screen access permission for admin roles."""

    screen_id: str
    allowed_roles: set[AdminRole]

    def is_accessible_by(self, role: AdminRole) -> bool:
        """Check if role can access this screen."""
        return role in self.allowed_roles


@dataclass
class AdminSession:
    """Active admin session with role-based permissions."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    role: AdminRole = AdminRole.VIEWER
    tenant_id: str | None = None
    permissions: set[AdminPermission] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    is_active: bool = True

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if session has permission for resource action."""
        if self.role == AdminRole.SUPER_ADMIN:
            return True

        return any(
            perm.matches(resource, action)
            for perm in self.permissions
        )

    def is_expired(self) -> bool:
        """Check if session is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_active = False


@dataclass
class PolicyChangeLogEntry:
    """Audit log entry for policy changes."""

    id: UUID = field(default_factory=uuid4)
    policy_id: str = ""
    policy_type: Literal["feature", "prompt"] = "feature"
    version: int = 1
    changed_by: UUID = field(default_factory=uuid4)
    change_type: Literal["create", "update", "rollback", "deactivate"] = "create"
    previous_version: int | None = None
    change_summary: str = ""
    change_details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "policy_id": self.policy_id,
            "policy_type": self.policy_type,
            "version": self.version,
            "changed_by": str(self.changed_by),
            "change_type": self.change_type,
            "previous_version": self.previous_version,
            "change_summary": self.change_summary,
            "change_details": self.change_details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MetricsSummary:
    """Aggregated metrics summary for dashboard."""

    period: Literal["daily", "weekly", "monthly"] = "daily"
    start_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Cost metrics
    total_cost: float = 0.0
    cost_by_feature: dict[str, float] = field(default_factory=dict)

    # Token metrics
    total_tokens: int = 0
    tokens_by_feature: dict[str, int] = field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # Invocation metrics
    total_invocations: int = 0
    invocations_by_feature: dict[str, int] = field(default_factory=dict)
    successful_invocations: int = 0
    failed_invocations: int = 0

    # Failure analysis
    failure_rate: float = 0.0
    failure_reasons: dict[str, int] = field(default_factory=dict)

    def calculate_failure_rate(self) -> None:
        """Calculate failure rate from invocations."""
        if self.total_invocations == 0:
            self.failure_rate = 0.0
        else:
            self.failure_rate = (self.failed_invocations / self.total_invocations) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "period": self.period,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_cost": self.total_cost,
            "cost_by_feature": self.cost_by_feature,
            "total_tokens": self.total_tokens,
            "tokens_by_feature": self.tokens_by_feature,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_invocations": self.total_invocations,
            "invocations_by_feature": self.invocations_by_feature,
            "successful_invocations": self.successful_invocations,
            "failed_invocations": self.failed_invocations,
            "failure_rate": self.failure_rate,
            "failure_reasons": self.failure_reasons,
        }
