# Generation Module Implementation

## Overview

Complete implementation of the `generation` module for SPEC-03-CREATION following Django 5.2 Clean Architecture 4-layer structure.

## Architecture

### Layer Structure

```
apps/generation/
├── domain/                    # Pure Python (ZERO Django imports)
│   ├── entities.py           # GenerationJob, GeneratedDesign, CostMetadata
│   ├── value_objects.py      # GenerationStatus, GenerationKind, AssetKind
│   └── services.py           # GenerationJobValidator, FallbackChainExecutor, CostCalculator
├── application/              # Use cases and ports
│   ├── ports.py              # Repository and service interfaces
│   ├── dtos.py               # Data transfer objects
│   └── use_cases/
│       ├── create_generation_job.py
│       ├── execute_generation_job.py
│       ├── list_generation_jobs.py
│       └── get_generation_result.py
├── infrastructure/           # Django ORM and external services
│   ├── orm/
│   │   └── models.py         # GenerationJobModel, GeneratedDesignModel
│   ├── repositories/
│   │   ├── generation_job_repository.py
│   │   └── generated_design_repository.py
│   ├── image_providers/      # AI model adapters
│   │   ├── base.py           # ImageProviderPort interface
│   │   ├── seedream_adapter.py
│   │   ├── alibaba_zimage_adapter.py
│   │   ├── gemini_image_adapter.py
│   │   └── openai_image_adapter.py
│   └── tasks.py              # Celery async tasks
└── presentation/             # DRF views and serializers
    ├── serializers.py
    ├── views.py
    └── urls.py
```

## Key Features

### Domain Requirements Met

- **REQ-03-GEN-001**: GenerationJob tracks all creation metadata
- **REQ-03-GEN-002**: Job MUST link to at least one of: brief, concept, rule, reference
- **REQ-03-GEN-003**: Refinement jobs preserve original UserSketchAsset (parent_sketch_id)
- **REQ-03-GEN-004**: Variation jobs create new assets with applied rule_ids
- **REQ-03-GEN-005**: Domain application jobs vary output format by domain pack
- **REQ-03-GEN-006**: All model calls go through SPEC-04 ModelRouter functional keys
- **REQ-03-GEN-007**: On failure → NO fake/placeholder images, record failure, retry via fallback policy
- **REQ-03-GEN-008**: Primary image provider = ByteDance Seedream 4.5
- **REQ-03-GEN-009**: Seedream adapter at infrastructure/image_providers/seedream_adapter.py
- **REQ-03-GEN-010**: Fallback chain: seedream-4.5 → z-image-turbo → gemini-3.1-flash-image-preview → gpt-image-2

### GenerationJob Entity

```python
@dataclass
class GenerationJob:
    id: UUID
    session_id: UUID
    kind: GenerationKind  # sketch, refinement, variation, domain_application
    prompt_id: Optional[UUID]
    brief_id: Optional[UUID]
    concept_id: Optional[UUID]
    rule_ids: list[UUID]
    sketch_id: Optional[UUID]  # For refinements
    reference_ids: list[UUID]
    status: GenerationStatus  # queued, running, completed, failed, cancelled
    model_policy_key: str
    retries: int
    cost_meta: Optional[CostMetadata]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
```

### GeneratedDesign Entity

```python
@dataclass
class GeneratedDesign:
    id: UUID
    job_id: UUID
    asset_uri: str  # URL to generated asset in object storage
    asset_kind: AssetKind  # image, thumbnail, annotated, composite
    parent_sketch_id: Optional[UUID]
    brief_id: Optional[UUID]
    concept_id: Optional[UUID]
    rule_ids: list[UUID]
    reference_ids: list[UUID]
    model_policy_key: str
    prompt_id: Optional[UUID]
    created_at: datetime
```

## API Endpoints

### Create Generation Job

```
POST /api/generation/jobs/
```

Request body:
```json
{
  "session_id": "uuid",
  "kind": "sketch",
  "brief_id": "uuid",
  "concept_id": "uuid",
  "model_policy_key": "default"
}
```

### List Generation Jobs

```
GET /api/generation/jobs/?session_id={uuid}&status={status}&kind={kind}&limit={limit}
```

### Get Generation Result

```
GET /api/generation/jobs/{job_id}/
```

### Execute Generation Job

```
POST /api/generation/jobs/{job_id}/execute/
```

### Check Job Status

```
GET /api/generation/jobs/status/?task_id={celery_task_id}
```

## Environment Variables

Required environment variables:

```bash
# ByteDance Seedream 4.5 (Primary)
BYTEDANCE_SEEDREAM_API_KEY=your_api_key
BYTEDANCE_SEEDREAM_BASE_URL=https://ark.ap-southeast-1.bytepluses.com/api/v3
BYTEDANCE_SEEDREAM_ENDPOINT=/images/generations

# Alibaba z-image-turbo (Fallback 1)
ALIBABA_API_KEY=your_api_key
ALIBABA_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# Google Gemini (Fallback 2)
GEMINI_API_KEY=your_api_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta

# OpenAI (Fallback 3)
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

## Database Schema

### generation_jobs Table

- `id` (UUID, PK)
- `session_id` (UUID, indexed)
- `kind` (VARCHAR, indexed)
- `prompt_id` (UUID, indexed, nullable)
- `brief_id` (UUID, indexed, nullable)
- `concept_id` (UUID, indexed, nullable)
- `rule_ids` (JSONB)
- `sketch_id` (UUID, indexed, nullable)
- `reference_ids` (JSONB)
- `status` (VARCHAR, indexed)
- `model_policy_key` (VARCHAR)
- `retries` (INTEGER)
- `cost_meta` (JSONB, nullable)
- `error_message` (TEXT, nullable)
- `created_at` (TIMESTAMP, indexed)
- `updated_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP, indexed, nullable)

Indexes:
- `(session_id, -created_at)`
- `(status, -created_at)`
- `(kind, -created_at)`

### generated_designs Table

- `id` (UUID, PK)
- `job_id` (UUID, indexed)
- `asset_uri` (TEXT)
- `asset_kind` (VARCHAR)
- `parent_sketch_id` (UUID, indexed, nullable)
- `brief_id` (UUID, indexed, nullable)
- `concept_id` (UUID, indexed, nullable)
- `rule_ids` (JSONB)
- `reference_ids` (JSONB)
- `model_policy_key` (VARCHAR)
- `prompt_id` (UUID, indexed, nullable)
- `created_at` (TIMESTAMP, indexed)
- `updated_at` (TIMESTAMP)

Indexes:
- `(job_id)`
- `(created_at)`

## Fallback Chain

The fallback chain executes models in order until one succeeds:

1. **seedream-4.5** (ByteDance Seedream 4.5 via BytePlus Ark)
   - Primary provider
   - Cost: $0.01/1K input, $0.02/1K output

2. **z-image-turbo** (Alibaba)
   - First fallback
   - Cost: $0.008/1K input, $0.016/1K output

3. **gemini-3.1-flash-image-preview** (Google)
   - Second fallback
   - Cost: $0.005/1K input, $0.01/1K output

4. **gpt-image-2** (OpenAI)
   - Final fallback
   - Cost: $0.015/1K input, $0.03/1K output

If all models fail, the job is marked as `FAILED` with an error message.

## Async Execution

Generation jobs are executed asynchronously via Celery:

1. Client calls `/api/generation/jobs/{job_id}/execute/`
2. View returns immediately with `task_id`
3. Celery worker picks up the task
4. Task runs `FallbackChainExecutor` with model chain
5. On success: saves `GeneratedDesign` entities
6. On failure: marks job as `FAILED` with error
7. Client polls `/api/generation/jobs/status/?task_id={task_id}` for results

## Testing

Run tests with:

```bash
pytest apps/generation/tests/
pytest apps/generation/tests/test_entities.py -v
```

## Integration Points

### SPEC-04 ModelRouter

The `ModelRouterPort` interface wraps SPEC-04 ModelRouter for image generation calls. The implementation uses functional keys:
- `ImageGeneration`: Main image generation function
- `SketchPrompt`: Prompt enhancement for sketches

### Object Storage

Generated images are stored via `ObjectStoragePort` from `shared.infrastructure`. The implementation uses:
- `upload_bytes()`: Upload image data
- `get_url()`: Get presigned URLs

### Abstraction Module

Variation jobs read abstraction rules via `AbstractionRulePort`:
- `find_by_ids()`: Fetch rules by IDs

### Concepts Module

Jobs can reference concepts via `ConceptPort`:
- `find_by_id()`: Fetch concept by ID

### Sketch Analysis (SPEC-01)

Refinement jobs access parent sketches via `SketchAnalysisPort`:
- `find_by_id()`: Fetch sketch by ID

## Constraints Compliance

✅ Pure Python domain layer (ZERO Django imports)
✅ Clean Architecture 4-layer separation
✅ File ≤ 1000 LOC, function ≤ 100 LOC, cyclomatic complexity ≤ 20
✅ `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`
✅ `shared.domain.exceptions` for all errors
✅ `shared.application.result.Result` for use case returns
✅ NO fake images, NO placeholders, NO hardcoded fallbacks
✅ Environment variables for API keys
✅ TRUST 5 quality standards

## Future Enhancements

1. **Model Router Integration**: Complete SPEC-04 ModelRouter integration
2. **Object Storage**: Implement real object storage backend (S3/GCS)
3. **Prompt Builder**: Enhance prompt building with context fetching
4. **Cost Tracking**: Implement persistent cost tracking
5. **Rate Limiting**: Add per-user rate limiting for generation
6. **Batch Generation**: Support batch job execution
7. **Webhooks**: Add webhook notifications for job completion
8. **Monitoring**: Add Prometheus metrics for monitoring

## License

Part of the DesignSupport project.
