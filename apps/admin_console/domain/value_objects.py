"""Value objects for admin console domain.

Pure Python value objects with no Django dependencies.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ModelType(str, Enum):
    """Model capability types."""

    TEXT = "text"
    CHAT = "chat"
    VISION = "vision"
    IMAGE = "image"
    SEARCH = "search"
    EMBEDDING = "embedding"
    MULTIMODAL = "multimodal"


@dataclass(frozen=True)
class FeatureKey:
    """Feature key identifier with validation."""

    key: str
    display_name: str
    description: str

    def __post_init__(self) -> None:
        """Validate feature key format."""
        if not self.key or len(self.key) > 100:
            raise ValueError("Feature key must be 1-100 characters")
        if not self.key.isalnum() and "_" not in self.key:
            raise ValueError("Feature key must be alphanumeric with underscores")


@dataclass(frozen=True)
class CostLimit:
    """Cost limit configuration."""

    max_cost_per_request: float
    max_cost_per_day: float
    max_cost_per_month: float
    currency: str = "USD"

    def __post_init__(self) -> None:
        """Validate cost limits."""
        if self.max_cost_per_request < 0:
            raise ValueError("Max cost per request cannot be negative")
        if self.max_cost_per_day < 0:
            raise ValueError("Max cost per day cannot be negative")
        if self.max_cost_per_month < 0:
            raise ValueError("Max cost per month cannot be negative")
        if self.max_cost_per_request > self.max_cost_per_day:
            raise ValueError("Max cost per request cannot exceed daily limit")
        if self.max_cost_per_day > self.max_cost_per_month:
            raise ValueError("Max daily cost cannot exceed monthly limit")


@dataclass(frozen=True)
class ModelCapabilities:
    """Model capability requirements."""

    required_types: set[ModelType]
    min_context_length: int = 4096
    supports_streaming: bool = False
    supports_function_calling: bool = False
    max_tokens_per_request: int = 4096

    def __post_init__(self) -> None:
        """Validate capabilities."""
        if not self.required_types:
            raise ValueError("At least one model type is required")
        if self.min_context_length < 1:
            raise ValueError("Min context length must be positive")
        if self.max_tokens_per_request < 1:
            raise ValueError("Max tokens per request must be positive")


@dataclass(frozen=True)
class FallbackChain:
    """Fallback model chain for resilience."""

    primary_model: str
    fallback_models: list[str]
    max_retries: int = 3
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        """Validate fallback chain."""
        if not self.primary_model:
            raise ValueError("Primary model is required")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.timeout_seconds < 1:
            raise ValueError("Timeout must be at least 1 second")
        if self.primary_model in self.fallback_models:
            raise ValueError("Primary model cannot be in fallback list")

    def get_full_chain(self) -> list[str]:
        """Get complete chain including primary."""
        return [self.primary_model] + self.fallback_models


@dataclass(frozen=True)
class PromptTemplate:
    """Prompt template for feature policies."""

    system_prompt: str
    user_template: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    def __post_init__(self) -> None:
        """Validate prompt template parameters."""
        if not self.system_prompt:
            raise ValueError("System prompt is required")
        if not self.user_template:
            raise ValueError("User template is required")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("Top-p must be between 0.0 and 1.0")
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValueError("Frequency penalty must be between -2.0 and 2.0")
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValueError("Presence penalty must be between -2.0 and 2.0")


@dataclass(frozen=True)
class AuditLogFilter:
    """Filter criteria for audit log queries."""

    actor_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    action_type: str | None = None
    start_date: str | None = None  # ISO format
    end_date: str | None = None  # ISO format
    tenant_id: str | None = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate filter parameters."""
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")


@dataclass(frozen=True)
class JobQueueFilter:
    """Filter criteria for job queue queries."""

    status: Literal["pending", "running", "failed", "completed"] | None = None
    job_type: str | None = None
    tenant_id: str | None = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        """Validate filter parameters."""
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
