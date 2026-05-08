# Model Catalog Module

Clean Architecture implementation for managing AI model providers, catalogs, and routing policies.

## Overview

This module implements SPEC-04-MODEL-ADMIN, providing a comprehensive system for:
- Registering and managing AI model providers
- Maintaining a catalog of available models
- Routing feature requests to appropriate models with fallback chains
- Tracking invocation metrics and costs
- Versioning policies with audit trails

## Architecture

Follows Django 5.2 Clean Architecture with 4 layers:

### Domain Layer (`domain/`)
Pure Python entities and services (ZERO Django imports).

**Entities:**
- `ModelProvider` - Provider configuration (API keys, base URLs)
- `ModelCatalog` - Model metadata (type, context limit, cost)
- `FeatureModelPolicy` - Feature-to-model mapping with fallbacks
- `PromptPolicy` - Prompt template management
- `ModelInvocation` - Invocation metrics tracking
- `PolicyChangeLog` - Audit trail for policy changes

**Services:**
- `ModelRouter` - Single entry point for model calls with fallback logic
- `PolicyVersionManager` - Policy versioning and rollback
- `CostGuard` - Cost estimation and blocking

### Application Layer (`application/`)
Use cases and repository ports.

**Use Cases:**
- `InvokeModelUseCase` - Route model calls
- `RegisterProviderUseCase` - Register new providers
- `RegisterModelUseCase` - Add models to catalog
- `UpdateFeaturePolicyUseCase` - Update policies (creates new version)
- `RollbackPolicyUseCase` - Rollback to previous policy version
- `GetModelMetricsUseCase` - Aggregate metrics
- `ListProvidersUseCase` - List providers
- `ListModelsUseCase` - List models with filters

**Ports:**
- Repository interfaces for all entities
- `ProviderAdapterPort` - Abstract interface for calling external APIs

### Infrastructure Layer (`infrastructure/`)
Django ORM models and repository implementations.

**ORM Models:**
- `ModelProviderModel`
- `ModelCatalogModel`
- `FeatureModelPolicyModel`
- `PromptPolicyModel`
- `ModelInvocationModel`
- `PolicyChangeLogModel`

**Repositories:**
- Async implementations of all repository ports using Django ORM

**Seed Data:**
- 4 providers: bytedance, alibaba, google, openai
- 9 feature policies (one per feature key)
- Initial models for each provider

**Management Commands:**
- `load_model_seeds` - Load seed data into database

### Presentation Layer (`presentation/`)
DRF serializers, views, and URL configuration.

**API Endpoints:**
- `GET /api/model-catalog/providers/` - List providers
- `POST /api/model-catalog/providers/register/` - Register provider
- `GET /api/model-catalog/models/` - List models
- `POST /api/model-catalog/models/register/` - Register model
- `POST /api/model-catalog/invocations/` - Invoke model
- `GET /api/model-catalog/policies/features/` - List feature policies
- `POST /api/model-catalog/policies/features/` - Create policy
- `PUT /api/model-catalog/policies/features/{id}/` - Update policy
- `POST /api/model-catalog/policies/features/{id}/rollback/` - Rollback policy
- `GET /api/model-catalog/metrics/` - Get metrics

## Feature Keys (REQ-04-POLICY-001)

Fixed set of 9 feature keys:
1. TrendResearch
2. ConceptChat
3. UserSketchAnalysis
4. ReferenceAnalysis
5. Abstraction
6. SketchPrompt
7. ImageGeneration
8. SpecWriting
9. Verification

## Model Types (REQ-04-CATALOG-002)

Supported model types:
- `text` - Text completion
- `chat` - Chat/completion
- `vision` - Image analysis
- `image` - Image generation
- `search` - Search/retrieval
- `embedding` - Embedding generation
- `multimodal` - Multi-modal models

## Usage

### Loading Seed Data

```bash
python manage.py load_model_seeds
```

This loads:
- 4 providers (bytedance, alibaba, google, openai)
- 6 models (2 per provider for ImageGeneration, chat models)
- 9 feature policies (one per feature key)

### Invoking a Model

```python
from apps.model_catalog.application.use_cases import InvokeModelUseCase
from apps.model_catalog.domain.services import ModelRouter
from apps.model_catalog.infrastructure.repositories import (
    FeatureModelPolicyRepository,
    ModelCatalogRepository,
    ModelInvocationRepository,
)

# Initialize router
router = ModelRouter(
    policy_repository=FeatureModelPolicyRepository(),
    model_repository=ModelCatalogRepository(),
    invocation_repository=ModelInvocationRepository(),
    cost_guard=None,
)

# Invoke model
use_case = InvokeModelUseCase(model_router=router)
result = use_case.execute(
    feature_key="ImageGeneration",
    payload={"prompt": "A beautiful sunset"},
    options={"quality": "high"},
    tenant_id="tenant-1",
    workspace_id="ws-1",
)

if result.is_success:
    response = result.value
    print(f"Model: {response['model_id']}")
    print(f"Tokens: {response['tokens_in']} + {response['tokens_out']}")
    print(f"Cost: ${response['cost_estimate']:.4f}")
```

### Registering a New Provider

```python
from apps.model_catalog.application.use_cases import RegisterProviderUseCase
from apps.model_catalog.infrastructure.repositories import ModelProviderRepository

use_case = RegisterProviderUseCase(
    provider_repository=ModelProviderRepository(),
)

result = use_case.execute(
    name="anthropic",
    api_key_env="ANTHROPIC_API_KEY",
    base_url="https://api.anthropic.com",
    auth_scheme="Bearer",
)

if result.is_success:
    provider = result.value
    print(f"Registered provider: {provider.id}")
```

### Updating a Feature Policy

```python
from apps.model_catalog.application.use_cases import UpdateFeaturePolicyUseCase

use_case = UpdateFeaturePolicyUseCase(
    policy_repository=FeatureModelPolicyRepository(),
    change_log_repository=PolicyChangeLogRepository(),
    version_manager=PolicyVersionManager(...),
)

result = use_case.execute(
    policy_id="policy-imagegeneration-v1",
    primary_model_id="mdl-new-model",
    fallback_model_ids=["mdl-fallback-1", "mdl-fallback-2"],
    actor_id="user-1",
    reason="Upgrading to better model",
)

if result.is_success:
    new_policy = result.value
    print(f"Created version {new_policy.version}")
```

## Invariants (REQ-04)

- **INV-04-01**: Model names/keys never hardcoded in code (use .env)
- **INV-04-02**: ModelRouter never produces fake results (ALL_MODELS_FAILED error)
- **INV-04-03**: Policy changes create new version (no destructive updates)

## Testing

### Domain Tests (Pure Python)
```bash
pytest apps/model_catalog/tests/test_domain.py
```

### Infrastructure Tests (Django)
```bash
pytest apps/model_catalog/tests/test_infrastructure.py --ds=config.settings.test
```

### API Tests
```bash
pytest apps/model_catalog/tests/test_api.py --ds=config.settings.test
```

## Database Schema

### model_providers
- id (PK)
- name (unique)
- api_key_env
- base_url
- endpoint_path
- auth_scheme
- active
- timestamps

### model_catalog
- id (PK)
- provider_id (FK)
- model_name
- type
- context_limit
- cost_estimate
- modalities (JSON)
- active
- timestamps
- unique: (provider, model_name)

### feature_model_policies
- id (PK)
- feature_key (unique)
- primary_model_id (FK)
- fallback_models (M2M)
- parameters (JSON)
- max_cost_per_call
- max_tokens
- version
- active
- reviewer
- timestamps

### model_invocations
- id (PK)
- feature_key
- tenant_id
- workspace_id
- session_id
- model_id (FK)
- status
- tokens_in
- tokens_out
- cost_estimate
- latency_ms
- error_code
- error_summary
- timestamps

### policy_change_logs
- id (PK)
- target_type
- target_id
- version_from
- version_to
- actor_id
- reason
- timestamps

## Dependencies

### Domain Layer
- Pure Python (no Django imports)
- `dataclasses`, `datetime`, `enum`, `typing`
- `shared.domain.exceptions`

### Application Layer
- Domain entities
- `shared.application.result`

### Infrastructure Layer
- Django 5.2 ORM
- Domain entities (for conversion)
- `shared.infrastructure.orm.base_model`

### Presentation Layer
- Django REST Framework
- Application use cases

## Future Enhancements

1. **Provider Adapters** - Implement `ProviderAdapterPort` for each provider
2. **CostGuard Implementation** - Real cost estimation and blocking
3. **Rate Limiting** - Per-feature rate limiting
4. **A/B Testing** - Multiple models per feature with traffic splitting
5. **Model Auto-Scaling** - Dynamic model selection based on load
6. **Metrics Dashboard** - Real-time metrics visualization

## References

- SPEC-04-MODEL-ADMIN
- REQ-04-CATALOG-001 through REQ-04-ROUTER-005
- INV-04-01 through INV-04-03
