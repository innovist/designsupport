"""Domain services for generation module.

This file is pure Python - no Django imports allowed.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from apps.generation.domain.entities import GenerationJob, CostMetadata
from apps.generation.domain.value_objects import GenerationKind
from shared.domain.exceptions import ValidationError, OperationError


class GenerationJobValidator:
    """Validator for generation job registration.

    REQ-03-GEN-002: Job MUST link to at least one of: brief, concept, rule, reference
    """

    def validate_job_creation(self, job: GenerationJob) -> None:
        """Validate that a job meets all requirements for creation.

        Args:
            job: The generation job to validate

        Raises:
            ValidationError: If job fails validation
        """
        # Check at least one context link
        has_brief = job.brief_id is not None
        has_concept = job.concept_id is not None
        has_rules = len(job.rule_ids) > 0
        has_references = len(job.reference_ids) > 0

        if not (has_brief or has_concept or has_rules or has_references):
            raise ValidationError(
                "context_links",
                "Job must link to at least one of: brief, concept, rule, or reference"
            )

        # Kind-specific validation
        if job.kind == GenerationKind.REFINEMENT and job.sketch_id is None:
            raise ValidationError(
                "sketch_id",
                "Refinement jobs require a parent sketch"
            )

        if job.kind == GenerationKind.VARIATION and len(job.rule_ids) == 0:
            raise ValidationError(
                "rule_ids",
                "Variation jobs require at least one abstraction rule"
            )

        if job.kind == GenerationKind.DOMAIN_APPLICATION and job.brief_id is None:
            raise ValidationError(
                "brief_id",
                "Domain application jobs require a brief"
            )


@dataclass
class ModelResult:
    """Result from a model generation attempt."""
    success: bool
    asset_uri: Optional[str] = None
    cost_meta: Optional[CostMetadata] = None
    error: Optional[str] = None
    model_key: Optional[str] = None


# @MX:WARN: [AUTO] Multi-provider fallback chain with cascading failure risk
# @MX:REASON: Sequential model attempts can cause latency; failure in all models blocks generation
# @MX:SPEC: REQ-03-GEN-010
class FallbackChainExecutor:
    """Executes model calls with fallback chain.

    REQ-03-GEN-010: Fallback chain for model providers
    """

    # Model fallback chain (ordered by preference)
    FALLBACK_CHAIN = [
        "seedream-4.5",  # ByteDance Seedream 4.5 (primary)
        "z-image-turbo",  # Alibaba z-image-turbo
        "gemini-3.1-flash-image-preview",  # Google Gemini
        "gpt-image-2",  # OpenAI GPT Image-2
    ]

    def __init__(self, model_router_port, max_retries_per_model: int = 1):
        """Initialize fallback chain executor.

        Args:
            model_router_port: ModelRouterPort for making model calls
            max_retries_per_model: Max retries per model before next fallback
        """
        self.model_router_port = model_router_port
        self.max_retries_per_model = max_retries_per_model

    # @MX:WARN: [AUTO] Async execution with external model provider dependencies
    # @MX:REASON: Each model call is I/O-bound; failure cascades through entire chain
    async def execute_with_fallback(
        self,
        prompt: str,
        model_policy_key: str,
        fallback_chain: Optional[list[str]] = None
    ) -> ModelResult:
        """Execute generation with fallback chain.

        Args:
            prompt: Generation prompt
            model_policy_key: Model routing policy key
            fallback_chain: Custom fallback chain (optional)

        Returns:
            ModelResult with success/failure details

        Raises:
            OperationError: If all models in chain fail
        """
        chain = fallback_chain or self.FALLBACK_CHAIN
        errors = []

        for model_key in chain:
            for attempt in range(self.max_retries_per_model):
                try:
                    # Call model through router
                    result = await self._call_model(
                        model_key=model_key,
                        prompt=prompt,
                        policy_key=model_policy_key
                    )

                    if result.success:
                        return ModelResult(
                            success=True,
                            asset_uri=result.asset_uri,
                            cost_meta=result.cost_meta,
                            model_key=model_key
                        )

                    errors.append(f"{model_key}: {result.error}")

                except Exception as e:
                    errors.append(f"{model_key}: {str(e)}")

        # All models failed
        raise OperationError(
            "fallback_chain",
            f"All models failed: {'; '.join(errors)}"
        )

    # @MX:ANCHOR: [AUTO] Single model invocation through SPEC-04 ModelRouter
    # @MX:REASON: All model calls must route through ModelRouter for cost tracking and policy enforcement
    # @MX:SPEC: REQ-03-GEN-006, REQ-04-ROUTER-001
    async def _call_model(
        self,
        model_key: str,
        prompt: str,
        policy_key: str
    ) -> ModelResult:
        """Call a single model through the router.

        REQ-03-GEN-006: All model calls go through SPEC-04 ModelRouter

        Args:
            model_key: Model identifier
            prompt: Generation prompt
            policy_key: Model routing policy key

        Returns:
            ModelResult from the model call
        """
        try:
            # This will be implemented by the ModelRouterPort adapter
            # The port wraps SPEC-04 ModelRouter functional keys
            result = await self.model_router_port.generate_image(
                model_key=model_key,
                prompt=prompt,
                policy_key=policy_key
            )

            return result

        except Exception as e:
            return ModelResult(
                success=False,
                error=str(e)
            )


# @MX:NOTE: [AUTO] Cost tracking per model with configurable token pricing
# @MX:REASON: Enables budget management and cost optimization across different model providers
# @MX:SPEC: REQ-03-GEN-003
class CostCalculator:
    """Calculator for tracking generation costs.

    REQ-03-GEN-003: Track cost metadata for generation calls
    """

    # Cost per 1K tokens (example rates - should be configurable)
    MODEL_COSTS = {
        "seedream-4.5": {"input": 0.01, "output": 0.02},
        "z-image-turbo": {"input": 0.008, "output": 0.016},
        "gemini-3.1-flash-image-preview": {"input": 0.005, "output": 0.01},
        "gpt-image-2": {"input": 0.015, "output": 0.03},
    }

    def calculate_cost(
        self,
        model_key: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> CostMetadata:
        """Calculate generation cost.

        Args:
            model_key: Model identifier
            prompt_tokens: Input tokens used
            completion_tokens: Output tokens used

        Returns:
            CostMetadata with calculated cost
        """
        if model_key not in self.MODEL_COSTS:
            # Use default rates if model not found
            rates = {"input": 0.01, "output": 0.02}
        else:
            rates = self.MODEL_COSTS[model_key]

        total_tokens = prompt_tokens + completion_tokens
        cost_usd = (
            (prompt_tokens / 1000.0) * rates["input"] +
            (completion_tokens / 1000.0) * rates["output"]
        )

        return CostMetadata(
            model_key=model_key,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=round(cost_usd, 6)
        )

    def estimate_cost(
        self,
        model_key: str,
        estimated_prompt_tokens: int
    ) -> float:
        """Estimate generation cost before execution.

        Args:
            model_key: Model identifier
            estimated_prompt_tokens: Estimated input tokens

        Returns:
            Estimated cost in USD
        """
        if model_key not in self.MODEL_COSTS:
            rates = {"input": 0.01, "output": 0.02}
        else:
            rates = self.MODEL_COSTS[model_key]

        # Assume output is ~2x input for image generation
        estimated_output_tokens = estimated_prompt_tokens * 2

        return (
            (estimated_prompt_tokens / 1000.0) * rates["input"] +
            (estimated_output_tokens / 1000.0) * rates["output"]
        )
