"""Domain entities for model catalog.

Pure Python domain entities with ZERO Django imports.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from shared.domain.exceptions import ValidationError


class ModelType(str, Enum):
    """Model type enumeration."""

    TEXT = "text"
    CHAT = "chat"
    VISION = "vision"
    IMAGE = "image"
    SEARCH = "search"
    EMBEDDING = "embedding"
    MULTIMODAL = "multimodal"


class AuthScheme(str, Enum):
    """Authentication scheme enumeration."""

    BEARER = "Bearer"
    API_KEY = "ApiKey"
    BASIC = "Basic"
    CUSTOM = "Custom"


class InvocationStatus(str, Enum):
    """Model invocation status enumeration."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class ModelProvider:
    """Model provider entity.

    Attributes:
        id: Unique provider identifier
        name: Provider name (e.g., "bytedance", "openai")
        api_key_env: Environment variable name containing API key
        base_url: Base URL for API endpoints
        endpoint_path: Default endpoint path
        auth_scheme: Authentication scheme
        active: Whether provider is active
    """

    id: str
    name: str
    api_key_env: str
    base_url: str | None = None
    endpoint_path: str | None = None
    auth_scheme: AuthScheme = AuthScheme.BEARER
    active: bool = True

    def __post_init__(self) -> None:
        """Validate provider data."""
        if not self.name:
            raise ValidationError("name", "Provider name cannot be empty")
        if not self.api_key_env:
            raise ValidationError("api_key_env", "API key environment variable cannot be empty")


@dataclass(frozen=True)
class ModelCatalog:
    """Model catalog entry entity.

    Attributes:
        id: Unique model identifier
        provider_id: Foreign key to ModelProvider
        model_name: Model name (e.g., "gpt-4", "seedream-4.5")
        type: Model type from ModelType enum
        context_limit: Maximum context window in tokens
        cost_estimate: Estimated cost per 1M tokens (USD)
        modalities: List of supported modalities
        active: Whether model is active
    """

    id: str
    provider_id: str
    model_name: str
    type: ModelType
    context_limit: int | None = None
    cost_estimate: float | None = None
    modalities: list[str] = field(default_factory=list)
    active: bool = True

    def __post_init__(self) -> None:
        """Validate model catalog data."""
        if not self.provider_id:
            raise ValidationError("provider_id", "Provider ID cannot be empty")
        if not self.model_name:
            raise ValidationError("model_name", "Model name cannot be empty")
        if self.context_limit is not None and self.context_limit <= 0:
            raise ValidationError("context_limit", "Context limit must be positive")
        if self.cost_estimate is not None and self.cost_estimate < 0:
            raise ValidationError("cost_estimate", "Cost estimate cannot be negative")

    @property
    def qualified_name(self) -> str:
        """Get fully qualified model name (provider/model)."""
        return f"{self.provider_id}/{self.model_name}"


@dataclass(frozen=True)
class FeatureModelPolicy:
    """Feature-to-model mapping policy entity.

    Attributes:
        id: Unique policy identifier
        feature_key: Feature identifier (one of 9 fixed keys)
        primary_model_id: Primary model ID for this feature
        fallback_model_ids: Ordered list of fallback model IDs
        parameters: Model-specific parameters (temperature, etc.)
        max_cost_per_call: Maximum allowed cost per call
        max_tokens: Maximum tokens per call
        version: Policy version number
        active: Whether this policy version is active
        reviewer: User who created/reviewed this policy
        created_at: Policy creation timestamp
    """

    id: str
    feature_key: str
    primary_model_id: str
    fallback_model_ids: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    max_cost_per_call: float | None = None
    max_tokens: int | None = None
    version: int = 1
    active: bool = True
    reviewer: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate feature policy data."""
        if not self.feature_key:
            raise ValidationError("feature_key", "Feature key cannot be empty")
        if not self.primary_model_id:
            raise ValidationError("primary_model_id", "Primary model ID cannot be empty")
        if self.max_cost_per_call is not None and self.max_cost_per_call < 0:
            raise ValidationError("max_cost_per_call", "Max cost per call cannot be negative")
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValidationError("max_tokens", "Max tokens must be positive")
        if self.version < 1:
            raise ValidationError("version", "Version must be at least 1")

    def get_model_chain(self) -> list[str]:
        """Get ordered chain of model IDs (primary + fallbacks)."""
        return [self.primary_model_id] + self.fallback_model_ids


@dataclass(frozen=True)
class PromptPolicy:
    """Prompt template policy entity.

    Attributes:
        id: Unique prompt policy identifier
        feature_key: Feature identifier
        prompt_version: Prompt version identifier
        system_prompt: System prompt template
        user_template: User prompt template with placeholders
        active: Whether this prompt policy is active
        reviewer: User who created/reviewed this policy
        created_at: Policy creation timestamp
    """

    id: str
    feature_key: str
    prompt_version: str
    system_prompt: str
    user_template: str
    active: bool = True
    reviewer: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate prompt policy data."""
        if not self.feature_key:
            raise ValidationError("feature_key", "Feature key cannot be empty")
        if not self.prompt_version:
            raise ValidationError("prompt_version", "Prompt version cannot be empty")
        if not self.system_prompt:
            raise ValidationError("system_prompt", "System prompt cannot be empty")
        if not self.user_template:
            raise ValidationError("user_template", "User template cannot be empty")


@dataclass
class ModelInvocation:
    """Model invocation metrics entity.

    Attributes:
        id: Unique invocation identifier
        feature_key: Feature that triggered the invocation
        tenant_id: Tenant identifier
        workspace_id: Workspace identifier
        session_id: Session identifier (optional)
        model_id: Model ID that was invoked
        status: Invocation status
        tokens_in: Input tokens used
        tokens_out: Output tokens generated
        cost_estimate: Estimated cost of this invocation
        latency_ms: Invocation latency in milliseconds
        error_code: Error code if failed
        error_summary: Error summary if failed
        created_at: Invocation timestamp
    """

    id: str
    feature_key: str
    tenant_id: str
    workspace_id: str
    model_id: str
    status: InvocationStatus
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_estimate: float | None = None
    latency_ms: int | None = None
    session_id: str | None = None
    error_code: str | None = None
    error_summary: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate invocation data."""
        if not self.feature_key:
            raise ValidationError("feature_key", "Feature key cannot be empty")
        if not self.tenant_id:
            raise ValidationError("tenant_id", "Tenant ID cannot be empty")
        if not self.workspace_id:
            raise ValidationError("workspace_id", "Workspace ID cannot be empty")
        if not self.model_id:
            raise ValidationError("model_id", "Model ID cannot be empty")
        if self.tokens_in is not None and self.tokens_in < 0:
            raise ValidationError("tokens_in", "Tokens in cannot be negative")
        if self.tokens_out is not None and self.tokens_out < 0:
            raise ValidationError("tokens_out", "Tokens out cannot be negative")
        if self.cost_estimate is not None and self.cost_estimate < 0:
            raise ValidationError("cost_estimate", "Cost estimate cannot be negative")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValidationError("latency_ms", "Latency cannot be negative")

    @property
    def total_tokens(self) -> int | None:
        """Get total tokens used (in + out)."""
        if self.tokens_in is None or self.tokens_out is None:
            return None
        return self.tokens_in + self.tokens_out

    @property
    def is_success(self) -> bool:
        """Check if invocation was successful."""
        return self.status == InvocationStatus.SUCCESS


@dataclass(frozen=True)
class PolicyChangeLog:
    """Policy change log entity.

    Attributes:
        id: Unique log entry identifier
        target_type: Type of policy that changed
        target_id: ID of the policy that changed
        version_from: Previous version number
        version_to: New version number
        actor_id: User who made the change
        reason: Reason for the change
        created_at: Change timestamp
    """

    id: str
    target_type: str
    target_id: str
    version_from: int | None
    version_to: int
    actor_id: str
    reason: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate change log data."""
        if not self.target_type:
            raise ValidationError("target_type", "Target type cannot be empty")
        if not self.target_id:
            raise ValidationError("target_id", "Target ID cannot be empty")
        if not self.actor_id:
            raise ValidationError("actor_id", "Actor ID cannot be empty")
        if self.version_to < 1:
            raise ValidationError("version_to", "Version to must be at least 1")
