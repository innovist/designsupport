"""Tests for model catalog domain layer.

Tests domain entities and services (pure Python, no Django).
"""
import pytest
from datetime import datetime

from apps.model_catalog.domain.entities import (
    AuthScheme,
    FeatureModelPolicy,
    ModelCatalog,
    ModelInvocation,
    ModelProvider,
    ModelType,
    PolicyChangeLog,
    PromptPolicy,
)
from shared.domain.exceptions import ValidationError


class TestModelProvider:
    """Tests for ModelProvider entity."""

    def test_create_valid_provider(self):
        """Test creating a valid provider."""
        provider = ModelProvider(
            id="prov-1",
            name="bytedance",
            api_key_env="BYTEDANCE_API_KEY",
            base_url="https://api.bytedance.com",
            auth_scheme=AuthScheme.BEARER,
            active=True,
        )

        assert provider.id == "prov-1"
        assert provider.name == "bytedance"
        assert provider.api_key_env == "BYTEDANCE_API_KEY"
        assert provider.base_url == "https://api.bytedance.com"
        assert provider.auth_scheme == AuthScheme.BEARER
        assert provider.active is True

    def test_provider_validation_empty_name(self):
        """Test provider validation fails with empty name."""
        with pytest.raises(ValidationError) as exc_info:
            ModelProvider(
                id="prov-1",
                name="",
                api_key_env="API_KEY",
            )

        assert "name" in str(exc_info.value)

    def test_provider_validation_empty_api_key_env(self):
        """Test provider validation fails with empty api_key_env."""
        with pytest.raises(ValidationError) as exc_info:
            ModelProvider(
                id="prov-1",
                name="provider",
                api_key_env="",
            )

        assert "api_key_env" in str(exc_info.value)


class TestModelCatalog:
    """Tests for ModelCatalog entity."""

    def test_create_valid_model(self):
        """Test creating a valid model catalog entry."""
        model = ModelCatalog(
            id="mdl-1",
            provider_id="prov-1",
            model_name="gpt-4",
            type=ModelType.CHAT,
            context_limit=128000,
            cost_estimate=0.005,
            modalities=["text", "vision"],
            active=True,
        )

        assert model.id == "mdl-1"
        assert model.provider_id == "prov-1"
        assert model.model_name == "gpt-4"
        assert model.type == ModelType.CHAT
        assert model.context_limit == 128000
        assert model.cost_estimate == 0.005
        assert model.modalities == ["text", "vision"]
        assert model.active is True

    def test_model_qualified_name(self):
        """Test model qualified_name property."""
        model = ModelCatalog(
            id="mdl-1",
            provider_id="prov-bytedance",
            model_name="seedream-4.5",
            type=ModelType.IMAGE,
        )

        assert model.qualified_name == "prov-bytedance/seedream-4.5"

    def test_model_validation_negative_context_limit(self):
        """Test model validation fails with negative context_limit."""
        with pytest.raises(ValidationError) as exc_info:
            ModelCatalog(
                id="mdl-1",
                provider_id="prov-1",
                model_name="gpt-4",
                type=ModelType.CHAT,
                context_limit=-100,
            )

        assert "context_limit" in str(exc_info.value)

    def test_model_validation_negative_cost(self):
        """Test model validation fails with negative cost_estimate."""
        with pytest.raises(ValidationError) as exc_info:
            ModelCatalog(
                id="mdl-1",
                provider_id="prov-1",
                model_name="gpt-4",
                type=ModelType.CHAT,
                cost_estimate=-0.01,
            )

        assert "cost_estimate" in str(exc_info.value)


class TestFeatureModelPolicy:
    """Tests for FeatureModelPolicy entity."""

    def test_create_valid_policy(self):
        """Test creating a valid feature policy."""
        policy = FeatureModelPolicy(
            id="policy-1",
            feature_key="ImageGeneration",
            primary_model_id="mdl-1",
            fallback_model_ids=["mdl-2", "mdl-3"],
            parameters={"quality": "high"},
            max_cost_per_call=0.05,
            max_tokens=1000,
            version=1,
            active=True,
        )

        assert policy.id == "policy-1"
        assert policy.feature_key == "ImageGeneration"
        assert policy.primary_model_id == "mdl-1"
        assert policy.fallback_model_ids == ["mdl-2", "mdl-3"]
        assert policy.parameters == {"quality": "high"}
        assert policy.max_cost_per_call == 0.05
        assert policy.max_tokens == 1000
        assert policy.version == 1
        assert policy.active is True

    def test_policy_get_model_chain(self):
        """Test get_model_chain returns primary + fallbacks."""
        policy = FeatureModelPolicy(
            id="policy-1",
            feature_key="ImageGeneration",
            primary_model_id="mdl-1",
            fallback_model_ids=["mdl-2", "mdl-3", "mdl-4"],
        )

        chain = policy.get_model_chain()
        assert chain == ["mdl-1", "mdl-2", "mdl-3", "mdl-4"]

    def test_policy_validation_empty_feature_key(self):
        """Test policy validation fails with empty feature_key."""
        with pytest.raises(ValidationError) as exc_info:
            FeatureModelPolicy(
                id="policy-1",
                feature_key="",
                primary_model_id="mdl-1",
            )

        assert "feature_key" in str(exc_info.value)

    def test_policy_validation_invalid_version(self):
        """Test policy validation fails with version < 1."""
        with pytest.raises(ValidationError) as exc_info:
            FeatureModelPolicy(
                id="policy-1",
                feature_key="ImageGeneration",
                primary_model_id="mdl-1",
                version=0,
            )

        assert "version" in str(exc_info.value)


class TestPromptPolicy:
    """Tests for PromptPolicy entity."""

    def test_create_valid_prompt_policy(self):
        """Test creating a valid prompt policy."""
        policy = PromptPolicy(
            id="prompt-1",
            feature_key="SpecWriting",
            prompt_version="v1.0",
            system_prompt="You are a helpful assistant.",
            user_template="Please write a spec for {topic}.",
            active=True,
        )

        assert policy.id == "prompt-1"
        assert policy.feature_key == "SpecWriting"
        assert policy.prompt_version == "v1.0"
        assert policy.system_prompt == "You are a helpful assistant."
        assert policy.user_template == "Please write a spec for {topic}."
        assert policy.active is True

    def test_prompt_policy_validation_empty_system_prompt(self):
        """Test prompt policy validation fails with empty system_prompt."""
        with pytest.raises(ValidationError) as exc_info:
            PromptPolicy(
                id="prompt-1",
                feature_key="SpecWriting",
                prompt_version="v1.0",
                system_prompt="",
                user_template="Template",
            )

        assert "system_prompt" in str(exc_info.value)


class TestModelInvocation:
    """Tests for ModelInvocation entity."""

    def test_create_successful_invocation(self):
        """Test creating a successful invocation record."""
        invocation = ModelInvocation(
            id="inv-1",
            feature_key="ImageGeneration",
            tenant_id="tenant-1",
            workspace_id="ws-1",
            model_id="mdl-1",
            status="success",  # type: ignore
            tokens_in=500,
            tokens_out=1000,
            cost_estimate=0.01,
            latency_ms=1500,
        )

        assert invocation.id == "inv-1"
        assert invocation.feature_key == "ImageGeneration"
        assert invocation.status == "success"
        assert invocation.tokens_in == 500
        assert invocation.tokens_out == 1000
        assert invocation.cost_estimate == 0.01
        assert invocation.latency_ms == 1500

    def test_invocation_total_tokens(self):
        """Test total_tokens property."""
        invocation = ModelInvocation(
            id="inv-1",
            feature_key="ImageGeneration",
            tenant_id="tenant-1",
            workspace_id="ws-1",
            model_id="mdl-1",
            status="success",  # type: ignore
            tokens_in=500,
            tokens_out=1000,
        )

        assert invocation.total_tokens == 1500

    def test_invocation_is_success(self):
        """Test is_success property."""
        invocation_success = ModelInvocation(
            id="inv-1",
            feature_key="ImageGeneration",
            tenant_id="tenant-1",
            workspace_id="ws-1",
            model_id="mdl-1",
            status="success",  # type: ignore
        )

        invocation_failure = ModelInvocation(
            id="inv-2",
            feature_key="ImageGeneration",
            tenant_id="tenant-1",
            workspace_id="ws-1",
            model_id="mdl-1",
            status="failure",  # type: ignore
        )

        assert invocation_success.is_success is True
        assert invocation_failure.is_success is False


class TestPolicyChangeLog:
    """Tests for PolicyChangeLog entity."""

    def test_create_valid_change_log(self):
        """Test creating a valid change log entry."""
        change_log = PolicyChangeLog(
            id="chg-1",
            target_type="feature",
            target_id="policy-1",
            version_from=1,
            version_to=2,
            actor_id="user-1",
            reason="Updated primary model",
        )

        assert change_log.id == "chg-1"
        assert change_log.target_type == "feature"
        assert change_log.target_id == "policy-1"
        assert change_log.version_from == 1
        assert change_log.version_to == 2
        assert change_log.actor_id == "user-1"
        assert change_log.reason == "Updated primary model"

    def test_change_log_validation_invalid_version_to(self):
        """Test change log validation fails with version_to < 1."""
        with pytest.raises(ValidationError) as exc_info:
            PolicyChangeLog(
                id="chg-1",
                target_type="feature",
                target_id="policy-1",
                version_from=1,
                version_to=0,
                actor_id="user-1",
                reason="Invalid version",
            )

        assert "version_to" in str(exc_info.value)


class TestModelTypeEnum:
    """Tests for ModelType enum."""

    def test_model_type_values(self):
        """Test ModelType enum has correct values."""
        assert ModelType.TEXT.value == "text"
        assert ModelType.CHAT.value == "chat"
        assert ModelType.VISION.value == "vision"
        assert ModelType.IMAGE.value == "image"
        assert ModelType.SEARCH.value == "search"
        assert ModelType.EMBEDDING.value == "embedding"
        assert ModelType.MULTIMODAL.value == "multimodal"

    def test_model_type_from_string(self):
        """Test creating ModelType from string."""
        model_type = ModelType("chat")
        assert model_type == ModelType.CHAT


class TestAuthSchemeEnum:
    """Tests for AuthScheme enum."""

    def test_auth_scheme_values(self):
        """Test AuthScheme enum has correct values."""
        assert AuthScheme.BEARER.value == "Bearer"
        assert AuthScheme.API_KEY.value == "ApiKey"
        assert AuthScheme.BASIC.value == "Basic"
        assert AuthScheme.CUSTOM.value == "Custom"
