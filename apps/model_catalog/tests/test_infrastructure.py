"""Tests for model catalog infrastructure layer (ORM models).

Tests Django ORM models and repositories.
"""
import pytest
from datetime import datetime

from apps.model_catalog.domain.entities import (
    AuthScheme,
    ModelProvider,
    ModelType,
)
from apps.model_catalog.infrastructure.orm.models import (
    ModelProviderModel,
    ModelCatalogModel,
)
from apps.model_catalog.infrastructure.seed_data import (
    PROVIDER_SEEDS,
    MODEL_SEEDS,
)


@pytest.mark.django_db
class TestModelProviderModel:
    """Tests for ModelProviderModel ORM."""

    def test_create_provider_from_domain(self):
        """Test creating ORM model from domain entity."""
        provider = ModelProvider(
            id="prov-test",
            name="test_provider",
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            auth_scheme=AuthScheme.BEARER,
            active=True,
        )

        orm_model = ModelProviderModel.from_domain(provider)
        orm_model.save()

        assert orm_model.id == "prov-test"
        assert orm_model.name == "test_provider"
        assert orm_model.api_key_env == "TEST_API_KEY"
        assert orm_model.base_url == "https://api.test.com"
        assert orm_model.auth_scheme == "Bearer"
        assert orm_model.active is True

    def test_convert_orm_to_domain(self):
        """Test converting ORM model to domain entity."""
        orm_model = ModelProviderModel.objects.create(
            id="prov-test",
            name="test_provider",
            api_key_env="TEST_API_KEY",
            auth_scheme="Bearer",
        )

        domain_entity = orm_model.to_domain()

        assert domain_entity.id == "prov-test"
        assert domain_entity.name == "test_provider"
        assert domain_entity.api_key_env == "TEST_API_KEY"
        assert domain_entity.auth_scheme == AuthScheme.BEARER


@pytest.mark.django_db
class TestModelCatalogModel:
    """Tests for ModelCatalogModel ORM."""

    def test_create_model_from_domain(self):
        """Test creating ORM model from domain entity."""
        # First create a provider
        provider = ModelProviderModel.objects.create(
            id="prov-test",
            name="test_provider",
            api_key_env="TEST_API_KEY",
        )

        from apps.model_catalog.domain.entities import ModelCatalog

        model = ModelCatalog(
            id="mdl-test",
            provider_id="prov-test",
            model_name="test-model",
            type=ModelType.CHAT,
            context_limit=128000,
            cost_estimate=0.005,
            modalities=["text", "vision"],
            active=True,
        )

        orm_model = ModelCatalogModel.from_domain(model)
        orm_model.save()

        assert orm_model.id == "mdl-test"
        assert orm_model.provider_id == "prov-test"
        assert orm_model.model_name == "test-model"
        assert orm_model.type == "chat"
        assert orm_model.context_limit == 128000
        assert orm_model.cost_estimate == 0.005
        assert orm_model.modalities == ["text", "vision"]
        assert orm_model.active is True

    def test_convert_orm_to_domain(self):
        """Test converting ORM model to domain entity."""
        provider = ModelProviderModel.objects.create(
            id="prov-test",
            name="test_provider",
            api_key_env="TEST_API_KEY",
        )

        orm_model = ModelCatalogModel.objects.create(
            id="mdl-test",
            provider=provider,
            model_name="test-model",
            type="chat",
            context_limit=128000,
            cost_estimate=0.005,
            modalities=["text"],
            active=True,
        )

        domain_entity = orm_model.to_domain()

        assert domain_entity.id == "mdl-test"
        assert domain_entity.provider_id == "prov-test"
        assert domain_entity.model_name == "test-model"
        assert domain_entity.type == ModelType.CHAT
        assert domain_entity.context_limit == 128000
        assert domain_entity.cost_estimate == 0.005
        assert domain_entity.modalities == ["text"]


@pytest.mark.django_db
class TestSeedData:
    """Tests for seed data loading."""

    def test_provider_seeds_are_valid(self):
        """Test that all provider seeds can be created."""
        for provider in PROVIDER_SEEDS:
            orm_model = ModelProviderModel.from_domain(provider)
            orm_model.save()

            saved = ModelProviderModel.objects.get(id=provider.id)
            assert saved.name == provider.name
            assert saved.api_key_env == provider.api_key_env

    def test_model_seeds_are_valid(self):
        """Test that all model seeds can be created (after providers)."""
        # First create providers
        for provider in PROVIDER_SEEDS:
            orm_model = ModelProviderModel.from_domain(provider)
            orm_model.save()

        # Then create models
        from apps.model_catalog.domain.entities import ModelCatalog

        for model in MODEL_SEEDS:
            domain_model = ModelCatalog(
                id=model.id,
                provider_id=model.provider_id,
                model_name=model.model_name,
                type=model.type,
                context_limit=model.context_limit,
                cost_estimate=model.cost_estimate,
                modalities=model.modalities,
                active=model.active,
            )
            orm_model = ModelCatalogModel.from_domain(domain_model)
            orm_model.save()

            saved = ModelCatalogModel.objects.get(id=model.id)
            assert saved.model_name == model.model_name
            assert saved.provider_id == model.provider_id
