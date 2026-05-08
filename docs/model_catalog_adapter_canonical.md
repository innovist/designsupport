# Model Catalog Adapter Architecture

## Overview

The model_catalog module implements a Clean Architecture pattern with provider adapters as the canonical implementation for all AI provider integrations.

## Architecture

### Canonical Implementations (apps/model_catalog/infrastructure/adapters/)

These adapters implement the `ProviderAdapterPort` interface and follow Clean Architecture principles:

- `seedream_adapter.py` - ByteDance Seedream 4.5 adapter
- `alibaba_zimage_adapter.py` - Alibaba Z-Image Turbo adapter
- `gemini_image_adapter.py` - Google Gemini image adapter
- `openai_image_adapter.py` - OpenAI GPT-Image-2 adapter

**Characteristics:**
- Domain-driven: Use domain entities (ModelProvider, ModelCatalog)
- Configurable: All settings from database, environment variables
- Testable: Implement ports for dependency injection
- No hardcoded values: API keys, URLs, model names from DB

### Legacy Clients (ai_clients/)

These are standalone clients that predate the model_catalog architecture:

- `seedream_client.py` - Seedream client with custom config
- `gemini_client.py` - Gemini client implementation
- `zimage_client.py` - Alibaba Z-Image client
- `nano_banana_client.py` - Google NanoBanana (Gemini) wrapper

**Characteristics:**
- Direct API implementations
- Hardcoded configurations
- Not integrated with model routing
- Duplicated logic

## Migration Strategy

### Current State (2026-05-08)

The ai_clients files still exist and may be used by existing code. **DO NOT DELETE** them without verifying no dependencies exist.

### Recommended Approach

**Phase 1: Update ai_clients to delegate to model_catalog adapters**

Instead of duplicating API logic, update ai_clients to use the canonical adapters:

```python
# ai_clients/seedream_client.py (RECOMMENDED PATTERN)
from apps.model_catalog.infrastructure.adapters.seedream_adapter import SeedreamAdapter
from apps.model_catalog.infrastructure.repositories import ModelProviderRepository

class SeedreamClient:
    def __init__(self):
        # Load provider and model from DB
        provider_repo = ModelProviderRepository()
        provider = provider_repo.get_by_name("bytedance")
        model = provider_repo.get_model("seedream-4.5")

        # Use canonical adapter
        self.adapter = SeedreamAdapter(provider, model)

    async def generate_image(self, prompt: str, **kwargs):
        # Delegate to adapter
        return await self.adapter.generate_image(prompt, **kwargs)
```

**Phase 2: Gradual migration**

1. Identify all usages of ai_clients files
2. Update imports to use model_catalog adapters
3. Remove duplicated logic from ai_clients
4. Keep ai_clients as thin wrappers if needed for backward compatibility

**Phase 3: Deprecation**

Once all code uses model_catalog adapters directly:
1. Mark ai_clients as deprecated
2. Add migration notes to documentation
3. Remove after grace period

## Benefits of Canonical Adapters

1. **Centralized Configuration**: All provider settings in database
2. **Dynamic Model Routing**: Automatic fallback chain support
3. **Cost Tracking**: Built-in invocation metrics
4. **Policy Enforcement**: Feature-based model selection
5. **Testability**: Mock ports for unit testing
6. **Maintainability**: Single source of truth for API logic

## Usage Example

```python
# NEW CODE: Use model_catalog directly
from apps.model_catalog.application.use_cases import ModelRoutingUseCase
from apps.model_catalog.domain.value_objects import FeatureKey

# Get model for feature
use_case = ModelRoutingUseCase()
model = use_case.get_model_for_feature(
    feature_key=FeatureKey.IMAGE_GENERATION,
    tenant_id="tenant-123"
)

# Generate image using adapter
result = await model.adapter.generate_image(prompt="fashion design")
```

## Migration Checklist

- [x] model_catalog adapters implemented
- [x] Seed data migration created (002_seed_providers_and_policies.py)
- [x] FeatureKey enum defined (domain/value_objects.py)
- [ ] Update ai_clients to delegate to model_catalog
- [ ] Find and update all ai_clients usage
- [ ] Add deprecation notices to ai_clients
- [ ] Remove ai_clients after migration complete

## Related Documentation

- SPEC-04-MODEL-ADMIN: Model catalog system specification
- apps/model_catalog/infrastructure/seed_data.py: Provider and policy seeds
- apps/model_catalog/domain/entities.py: Domain entity definitions

---

**Last Updated:** 2026-05-08
**Status:** model_catalog adapters are canonical implementations
**Action Required:** Migrate ai_clients to delegate to adapters
