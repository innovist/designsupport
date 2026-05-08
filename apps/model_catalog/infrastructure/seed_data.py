"""Seed data for model catalog.

Implements REQ-04-POLICY-006 and REQ-04-POLICY-007: Provider and policy seeds.
"""
import uuid

from apps.model_catalog.domain.entities import (
    AuthScheme,
    FeatureModelPolicy,
    ModelCatalog,
    ModelProvider,
    ModelType,
)


# Seed providers (REQ-04-POLICY-007)
PROVIDER_SEEDS = [
    ModelProvider(
        id="prov-bytedance",
        name="bytedance",
        api_key_env="BYTEDANCE_SEEDREAM_API_KEY",
        base_url="https://ark.ap-southeast.bytepluses.com/api/v3",
        endpoint_path="/images/generations",
        auth_scheme=AuthScheme.BEARER,
        active=True,
    ),
    ModelProvider(
        id="prov-alibaba",
        name="alibaba",
        api_key_env="ALIBABA_API_KEY",
        auth_scheme=AuthScheme.BEARER,
        active=True,
    ),
    ModelProvider(
        id="prov-google",
        name="google",
        api_key_env="GEMINI_API_KEYS",
        auth_scheme=AuthScheme.BEARER,
        active=True,
    ),
    ModelProvider(
        id="prov-openai",
        name="openai",
        api_key_env="OPENAI_API_KEY",
        auth_scheme=AuthScheme.BEARER,
        active=True,
    ),
]


# Seed models for each provider
MODEL_SEEDS = [
    # ByteDance models
    ModelCatalog(
        id="mdl-bytedance-seedream-4.5",
        provider_id="prov-bytedance",
        model_name="seedream-4.5",
        type=ModelType.IMAGE,
        context_limit=None,
        cost_estimate=0.02,
        modalities=["image"],
        active=True,
    ),
    # Alibaba models
    ModelCatalog(
        id="mdl-alibaba-z-image-turbo",
        provider_id="prov-alibaba",
        model_name="z-image-turbo",
        type=ModelType.IMAGE,
        context_limit=None,
        cost_estimate=0.015,
        modalities=["image"],
        active=True,
    ),
    # Google models
    ModelCatalog(
        id="mdl-google-gemini-3.1-flash-image-preview",
        provider_id="prov-google",
        model_name="gemini-3.1-flash-image-preview",
        type=ModelType.MULTIMODAL,
        context_limit=28000,
        cost_estimate=0.001,
        modalities=["text", "image", "vision"],
        active=True,
    ),
    ModelCatalog(
        id="mdl-google-gemini-2.5-pro",
        provider_id="prov-google",
        model_name="gemini-2.5-pro",
        type=ModelType.CHAT,
        context_limit=1000000,
        cost_estimate=0.002,
        modalities=["text", "code"],
        active=True,
    ),
    # OpenAI models
    ModelCatalog(
        id="mdl-openai-gpt-image-2",
        provider_id="prov-openai",
        model_name="gpt-image-2",
        type=ModelType.IMAGE,
        context_limit=None,
        cost_estimate=0.03,
        modalities=["image"],
        active=True,
    ),
    ModelCatalog(
        id="mdl-openai-gpt-4o",
        provider_id="prov-openai",
        model_name="gpt-4o",
        type=ModelType.CHAT,
        context_limit=128000,
        cost_estimate=0.005,
        modalities=["text", "vision"],
        active=True,
    ),
]


# 9 Feature Keys (REQ-04-POLICY-001)
FEATURE_KEYS = [
    "TrendResearch",
    "ConceptChat",
    "UserSketchAnalysis",
    "ReferenceAnalysis",
    "Abstraction",
    "SketchPrompt",
    "ImageGeneration",
    "SpecWriting",
    "Verification",
]


# Seed feature policies (REQ-04-POLICY-006)
FEATURE_POLICY_SEEDS = [
    # ImageGeneration: specific seed with fallback chain
    FeatureModelPolicy(
        id="policy-imagegeneration-v1",
        feature_key="ImageGeneration",
        primary_model_id="mdl-bytedance-seedream-4.5",
        fallback_model_ids=[
            "mdl-alibaba-z-image-turbo",
            "mdl-google-gemini-3.1-flash-image-preview",
            "mdl-openai-gpt-image-2",
        ],
        parameters={"quality": "high", "size": "1024x1024"},
        max_cost_per_call=0.05,
        max_tokens=None,
        version=1,
        active=True,
        reviewer="system",
    ),
    # Other features: use reasonable defaults (chat/text models)
    FeatureModelPolicy(
        id="policy-trendresearch-v1",
        feature_key="TrendResearch",
        primary_model_id="mdl-google-gemini-2.5-pro",
        fallback_model_ids=[],
        parameters={"temperature": 0.7, "max_tokens": 2000},
        max_cost_per_call=0.01,
        max_tokens=2000,
        version=1,
        active=True,
        reviewer="system",
    ),
    FeatureModelPolicy(
        id="policy-conceptchat-v1",
        feature_key="ConceptChat",
        primary_model_id="mdl-google-gemini-2.5-pro",
        fallback_model_ids=[],
        parameters={"temperature": 0.8, "max_tokens": 1500},
        max_cost_per_call=0.01,
        max_tokens=1500,
        version=1,
        active=True,
        reviewer="system",
    ),
    FeatureModelPolicy(
        id="policy-usersketchanalysis-v1",
        feature_key="UserSketchAnalysis",
        primary_model_id="mdl-google-gemini-3.1-flash-image-preview",
        fallback_model_ids=[],
        parameters={"temperature": 0.5},
        max_cost_per_call=0.01,
        max_tokens=1000,
        version=1,
        active=True,
        reviewer="system",
    ),
    FeatureModelPolicy(
        id="policy-referenceanalysis-v1",
        feature_key="ReferenceAnalysis",
        primary_model_id="mdl-google-gemini-2.5-pro",
        fallback_model_ids=[],
        parameters={"temperature": 0.6, "max_tokens": 2000},
        max_cost_per_call=0.01,
        max_tokens=2000,
        version=1,
        active=True,
        reviewer="system",
    ),
    FeatureModelPolicy(
        id="policy-abstraction-v1",
        feature_key="Abstraction",
        primary_model_id="mdl-google-gemini-2.5-pro",
        fallback_model_ids=[],
        parameters={"temperature": 0.7, "max_tokens": 1500},
        max_cost_per_call=0.01,
        max_tokens=1500,
        version=1,
        active=True,
        reviewer="system",
    ),
    FeatureModelPolicy(
        id="policy-sketchprompt-v1",
        feature_key="SketchPrompt",
        primary_model_id="mdl-google-gemini-2.5-pro",
        fallback_model_ids=[],
        parameters={"temperature": 0.8, "max_tokens": 1000},
        max_cost_per_call=0.01,
        max_tokens=1000,
        version=1,
        active=True,
        reviewer="system",
    ),
    FeatureModelPolicy(
        id="policy-specwriting-v1",
        feature_key="SpecWriting",
        primary_model_id="mdl-google-gemini-2.5-pro",
        fallback_model_ids=[],
        parameters={"temperature": 0.6, "max_tokens": 3000},
        max_cost_per_call=0.02,
        max_tokens=3000,
        version=1,
        active=True,
        reviewer="system",
    ),
    FeatureModelPolicy(
        id="policy-verification-v1",
        feature_key="Verification",
        primary_model_id="mdl-google-gemini-2.5-pro",
        fallback_model_ids=[],
        parameters={"temperature": 0.3, "max_tokens": 2000},
        max_cost_per_call=0.01,
        max_tokens=2000,
        version=1,
        active=True,
        reviewer="system",
    ),
]


def get_all_seeds():
    """Get all seed data."""
    return {
        "providers": PROVIDER_SEEDS,
        "models": MODEL_SEEDS,
        "feature_policies": FEATURE_POLICY_SEEDS,
    }
