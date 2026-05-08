# Image Provider Adapters - Quick Start Guide

## Setup

1. **Install dependencies** (already in requirements.txt):
   - httpx>=0.27.0
   - Django>=5.2

2. **Configure environment variables** in `.env`:
   ```bash
   BYTEDANCE_SEEDREAM_API_KEY=your_key_here
   ALIBABA_API_KEY=your_key_here
   GEMINI_API_KEYS=your_key_here
   OPENAI_API_KEY=your_key_here
   ```

3. **Run database migration**:
   ```bash
   alembic upgrade head
   ```

This will seed the database with:
- 4 providers (bytedance, alibaba, google, openai)
- 6 models (seedream-4.5, z-image-turbo, gemini-3.1-flash-image-preview, gpt-image-2, gemini-2.5-pro, gpt-4o)
- 9 feature policies with fallback chains

## Usage

### Option 1: Via ModelRouter (Recommended)

```python
from apps.model_catalog.domain.services import ModelRouter

# Inject repositories (depends on your setup)
router = ModelRouter(
    policy_repository=policy_repo,
    model_repository=model_repo,
    invocation_repository=invocation_repo,
    cost_guard=cost_guard,
)

# Generate image with automatic fallback
response, invocation = await router.invoke(
    feature_key="ImageGeneration",
    payload={
        "prompt": "A serene mountain landscape at sunset",
        "size": "1024x1024",
        "n": 1,
    },
    options={},
    tenant_id="tenant-123",
    workspace_id="workspace-456",
    session_id="session-789",  # optional
)

# Access results
image_url = response["asset_uri"]
cost_meta = response["cost_meta"]
print(f"Image: {image_url}")
print(f"Model: {invocation.model_id}")
print(f"Cost: ${cost_meta.cost_usd:.4f}")
print(f"Latency: {invocation.latency_ms}ms")
```

### Option 2: Direct Adapter Usage

```python
from apps.generation.infrastructure.image_providers.seedream_adapter import SeedreamAdapter
from apps.model_catalog.domain.entities import ModelProvider, ModelCatalog, AuthScheme

# Create provider and model entities
provider = ModelProvider(
    id="prov-bytedance",
    name="bytedance",
    api_key_env="BYTEDANCE_SEEDREAM_API_KEY",
    base_url="https://ark.ap-southeast.bytepluses.com/api/v3",
    endpoint_path="/images/generations",
    auth_scheme=AuthScheme.BEARER,
    active=True,
)

model = ModelCatalog(
    id="mdl-bytedance-seedream-4.5",
    provider_id="prov-bytedance",
    model_name="seedream-4.5",
    type="image",
    cost_estimate=0.02,
    modalities=["image"],
    active=True,
)

# Create adapter
adapter = SeedreamAdapter(provider, model)

# Generate image
result = await adapter.generate_image(
    prompt="A futuristic city with flying cars",
    size="1024x1024",
    n=1,
)

# Check result
if result.is_success:
    image_url = result.value["asset_uri"]
    cost_meta = result.value["cost_meta"]
    print(f"Success! Image URL: {image_url}")
    print(f"Cost: ${cost_meta.cost_usd:.4f}")
else:
    print(f"Error: {result.error}")
```

## Available Providers

| Provider | Model | Cost/Image | Response Type | Environment Variable |
|----------|-------|-----------|---------------|---------------------|
| ByteDance | seedream-4.5 | $0.02 | URL | BYTEDANCE_SEEDREAM_API_KEY |
| Alibaba | z-image-turbo | $0.015 | URL | ALIBABA_API_KEY |
| Google | gemini-3.1-flash-image-preview | $0.01 | Base64 | GEMINI_API_KEYS |
| OpenAI | gpt-image-2 | $0.04 | URL | OPENAI_API_KEY |

## Feature Policies

The system includes 9 pre-configured feature policies:

1. **ImageGeneration**: Primary=seedream-4.5, Fallback=[z-image-turbo, gemini-3.1-flash-image-preview, gpt-image-2]
2. **TrendResearch**: Primary=gemini-2.5-pro
3. **ConceptChat**: Primary=gemini-2.5-pro
4. **UserSketchAnalysis**: Primary=gemini-3.1-flash-image-preview
5. **ReferenceAnalysis**: Primary=gemini-2.5-pro
6. **Abstraction**: Primary=gemini-2.5-pro
7. **SketchPrompt**: Primary=gemini-2.5-pro
8. **SpecWriting**: Primary=gemini-2.5-pro
9. **Verification**: Primary=gemini-2.5-pro

## Error Handling

All adapters raise `OperationError` with descriptive messages:

```python
from shared.domain.exceptions import OperationError

try:
    result = await adapter.generate_image(prompt="test")
except OperationError as e:
    if "API key not found" in str(e):
        print("Missing environment variable")
    elif "timed out" in str(e):
        print("Request timeout - check network")
    elif "status 429" in str(e):
        print("Rate limited - wait and retry")
    else:
        print(f"Error: {e}")
```

## Cost Estimation

Before generating an image, estimate the cost:

```python
adapter = SeedreamAdapter(provider, model)
estimated_cost = adapter.estimate_cost()
print(f"Estimated cost: ${estimated_cost:.4f}")
```

## Supported Image Sizes

All providers support standard sizes:
- `1024x1024` (default)
- `512x512`
- `256x256`

Note: Some providers may support additional sizes (e.g., `1792x1024` for OpenAI).

## Testing

Run the provided tests:

```bash
# Unit tests (mocked)
pytest apps/generation/tests/unit/test_image_providers.py

# Integration tests (requires real API keys)
pytest apps/generation/tests/integration/test_image_providers_integration.py
```

## Troubleshooting

**Problem**: "API key not found in environment variable"
**Solution**: Ensure the environment variable is set in `.env` and loaded

**Problem**: "API request timed out after 60 seconds"
**Solution**: Check network connectivity or increase timeout in adapter

**Problem**: "API request failed with status 401"
**Solution**: Verify API key is valid and active

**Problem**: "Invalid response format: missing 'data' field"
**Solution**: API response format may have changed - check adapter implementation

## Database Schema

After migration, your database will have:

- `model_providers` table with 4 providers
- `model_catalog` table with 6 models
- `feature_model_policies` table with 9 policies
- `feature_model_policies_fallback_models` table with fallback relationships

## Monitoring

Track image generation metrics via `ModelInvocation` records:

```python
# Get recent invocations
invocations = await ModelInvocationModel.objects.filter(
    feature_key="ImageGeneration"
).order_by('-created_at')[:10]

for inv in invocations:
    print(f"Model: {inv.model_id}")
    print(f"Status: {inv.status}")
    print(f"Cost: ${inv.cost_estimate:.4f}")
    print(f"Latency: {inv.latency_ms}ms")
    if inv.error_code:
        print(f"Error: {inv.error_code} - {inv.error_summary}")
```

## Performance Tips

1. **Use fallback chains**: Configure multiple providers for reliability
2. **Cache results**: Store generated images to avoid regenerating
3. **Monitor costs**: Track actual API costs vs estimates
4. **Set rate limits**: Prevent API quota exhaustion
5. **Handle timeouts**: Implement retry logic with exponential backoff

## Next Steps

1. Configure real API keys in `.env`
2. Test with small prompts first
3. Monitor actual costs vs estimates
4. Adjust cost estimates based on real usage
5. Implement caching for frequently generated images
6. Add rate limiting to prevent quota exhaustion
7. Set up monitoring/alerting for failed generations

## Support

For issues or questions:
- Check implementation docs: `IMPLEMENTATION_SUMMARY.md`
- Review integration tests: `apps/generation/tests/integration/test_image_providers_integration.py`
- Examine adapter source code in `apps/generation/infrastructure/image_providers/`
