"""Django ORM models for admin console.

Maps domain entities to database tables.
"""
from django.db import models
from uuid import uuid4

from shared.infrastructure.orm.base_model import TimestampedModel


class AdminSessionORM(TimestampedModel):
    """ORM model for AdminSession entity."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ("super_admin", "Super Admin"),
            ("tenant_admin", "Tenant Admin"),
            ("viewer", "Viewer"),
        ],
        default="viewer",
    )
    tenant_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "admin_sessions"
        indexes = [
            models.Index(fields=["user_id", "is_active"]),
            models.Index(fields=["tenant_id", "is_active"]),
        ]
        ordering = ["-created_at"]

    def to_domain(self):
        """Convert to domain entity."""
        from apps.admin_console.domain.entities import AdminSession, AdminRole

        return AdminSession(
            id=self.id,
            user_id=self.user_id,
            role=AdminRole(self.role),
            tenant_id=self.tenant_id,
            permissions=set(),  # Load from separate table if needed
            created_at=self.created_at,
            expires_at=self.expires_at,
            is_active=self.is_active,
        )


class PolicyChangeLogORM(TimestampedModel):
    """ORM model for PolicyChangeLogEntry entity."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    policy_id = models.CharField(max_length=255, db_index=True)
    policy_type = models.CharField(
        max_length=20,
        choices=[
            ("feature", "Feature Policy"),
            ("prompt", "Prompt Policy"),
        ],
        default="feature",
    )
    version = models.IntegerField(db_index=True)
    changed_by = models.UUIDField(db_index=True)
    change_type = models.CharField(
        max_length=20,
        choices=[
            ("create", "Create"),
            ("update", "Update"),
            ("rollback", "Rollback"),
            ("deactivate", "Deactivate"),
        ],
        default="create",
    )
    previous_version = models.IntegerField(null=True, blank=True)
    change_summary = models.TextField()
    change_details = models.JSONField(default=dict)

    class Meta:
        db_table = "policy_change_log"
        indexes = [
            models.Index(fields=["policy_id", "-version"]),
            models.Index(fields=["policy_type", "-created_at"]),
            models.Index(fields=["changed_by", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def to_domain(self):
        """Convert to domain entity."""
        from apps.admin_console.domain.entities import PolicyChangeLogEntry

        return PolicyChangeLogEntry(
            id=self.id,
            policy_id=self.policy_id,
            policy_type=self.policy_type,  # type: ignore
            version=self.version,
            changed_by=self.changed_by,
            change_type=self.change_type,  # type: ignore
            previous_version=self.previous_version,
            change_summary=self.change_summary,
            change_details=self.change_details,
            timestamp=self.created_at,
        )


class AdminMetricsORM(models.Model):
    """ORM model for cached metrics summaries."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    period = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        db_index=True,
    )
    start_date = models.DateTimeField(db_index=True)
    end_date = models.DateTimeField(db_index=True)
    feature_key = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    # Cost metrics
    total_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0.0)
    cost_by_feature = models.JSONField(default=dict)

    # Token metrics
    total_tokens = models.BigIntegerField(default=0)
    tokens_by_feature = models.JSONField(default=dict)
    prompt_tokens = models.BigIntegerField(default=0)
    completion_tokens = models.BigIntegerField(default=0)

    # Invocation metrics
    total_invocations = models.IntegerField(default=0)
    invocations_by_feature = models.JSONField(default=dict)
    successful_invocations = models.IntegerField(default=0)
    failed_invocations = models.IntegerField(default=0)

    # Failure analysis
    failure_rate = models.FloatField(default=0.0)
    failure_reasons = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_metrics"
        indexes = [
            models.Index(fields=["period", "-start_date"]),
            models.Index(fields=["feature_key", "period", "-start_date"]),
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["-start_date"]


class FeaturePolicyORM(TimestampedModel):
    """ORM model for feature policies."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature_key = models.CharField(max_length=100, unique=True, db_index=True)
    version = models.IntegerField(default=1, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Model configuration
    model_type = models.CharField(max_length=50)
    primary_model = models.CharField(max_length=255)
    fallback_models = models.JSONField(default=list)
    max_retries = models.IntegerField(default=3)
    timeout_seconds = models.IntegerField(default=30)

    # Cost limits
    max_cost_per_request = models.DecimalField(max_digits=10, decimal_places=4)
    max_cost_per_day = models.DecimalField(max_digits=12, decimal_places=4)
    max_cost_per_month = models.DecimalField(max_digits=14, decimal_places=4)
    currency = models.CharField(max_length=3, default="USD")

    # Capabilities
    required_model_types = models.JSONField(default=list)
    min_context_length = models.IntegerField(default=4096)
    supports_streaming = models.BooleanField(default=False)
    supports_function_calling = models.BooleanField(default=False)
    max_tokens_per_request = models.IntegerField(default=4096)

    # Metadata
    created_by = models.UUIDField(db_index=True)
    modified_by = models.UUIDField(db_index=True)
    change_reason = models.TextField(blank=True)

    class Meta:
        db_table = "feature_policies"
        indexes = [
            models.Index(fields=["feature_key", "-version"]),
            models.Index(fields=["is_active", "feature_key"]),
        ]
        ordering = ["feature_key", "-version"]


class PromptPolicyORM(TimestampedModel):
    """ORM model for prompt policies."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature_key = models.CharField(max_length=100, unique=True, db_index=True)
    version = models.IntegerField(default=1, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Prompt templates
    system_prompt = models.TextField()
    user_template = models.TextField()

    # Generation parameters
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2048)
    top_p = models.FloatField(default=0.9)
    frequency_penalty = models.FloatField(default=0.0)
    presence_penalty = models.FloatField(default=0.0)

    # Metadata
    created_by = models.UUIDField(db_index=True)
    modified_by = models.UUIDField(db_index=True)
    change_reason = models.TextField(blank=True)

    class Meta:
        db_table = "admin_prompt_policies"
        indexes = [
            models.Index(fields=["feature_key", "-version"]),
            models.Index(fields=["is_active", "feature_key"]),
        ]
        ordering = ["feature_key", "-version"]


class TenantORM(TimestampedModel):
    """ORM model for tenant management."""

    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)
    plan = models.CharField(
        max_length=50,
        choices=[
            ("free", "Free"),
            ("pro", "Pro"),
            ("enterprise", "Enterprise"),
        ],
        default="free",
    )

    # Limits
    max_users = models.IntegerField(default=5)
    max_projects = models.IntegerField(default=10)
    max_storage_gb = models.IntegerField(default=10)

    # Metadata
    created_by = models.UUIDField()
    settings = models.JSONField(default=dict)

    class Meta:
        db_table = "admin_tenants"
        indexes = [
            models.Index(fields=["is_active", "plan"]),
            models.Index(fields=["-created_at"]),
        ]
        ordering = ["name"]


class UserTenantRoleORM(models.Model):
    """ORM model for user-tenant-role associations."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    tenant_id = models.CharField(max_length=255, db_index=True)
    role = models.CharField(
        max_length=50,
        choices=[
            ("owner", "Owner"),
            ("admin", "Admin"),
            ("member", "Member"),
            ("viewer", "Viewer"),
        ],
        default="member",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_tenant_roles"
        unique_together = [["user_id", "tenant_id"]]
        indexes = [
            models.Index(fields=["tenant_id", "role"]),
            models.Index(fields=["user_id", "is_active"]),
        ]
        ordering = ["tenant_id", "role"]
