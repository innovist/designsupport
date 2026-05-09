# Research: SPEC-01-FOUNDATION-SESSION

Codebase analysis for foundation, session management, multi-tenancy, and project structure.

## Current Codebase State

### ORM & Database

| Aspect | Current | SPEC Target | Gap |
|--------|---------|-------------|-----|
| ORM | SQLAlchemy (declarative_base) | Django ORM | CRITICAL - full rewrite |
| Database | SQLite (`storage/fashion.db`) | PostgreSQL 14+ | CRITICAL - migration needed |
| Engine | `create_engine()` with `pool_pre_ping` | Django DATABASES config | CRITICAL |
| Session mgmt | `sessionmaker` + `get_db()` generator | Django ORM + Celery | Full replacement |
| Migration | `Base.metadata.create_all()` | Alembic → Django migrations | Full replacement |

### Models Analysis (14 files, 14,438 total LOC)

**BaseModel** (`app/models/base.py`, 94 LOC):
- Uses `declarative_base()` from SQLAlchemy
- `TimestampMixin`: created_at, updated_at (server_default=func.now())
- `SoftDeleteMixin`: deleted_at, is_deleted
- `BaseModel(Base, TimestampMixin)`: id (Integer PK), metadata_json (JSON), notes (Text)
- `to_dict()` method for serialization
- Reusable for Django but needs complete rewrite

**User** (`app/models/user.py`, 163 LOC):
- Fields: email, username, password_hash, full_name, role (Enum), is_active, is_verified, language, size_standard, timezone, api_quota_daily/monthly, last_login_at, password_changed_at
- UserRole enum: admin, designer, analyst, viewer
- Close alignment with SPEC-01 Account entity
- MISSING: Tenant FK, Workspace FK, Membership relationship
- MISSING: tenant_id on all data rows (multi-tenancy)

**Project** (`app/models/project.py`, 264 LOC):
- Fields: title, description, owner_id, status (Enum), progress_percent, prompt, gender, age_group, season, region, target_audience, language, size_standard, crawl_sources/keywords, max_crawl_pages, preferred_image_model
- ProjectStatus: draft/active/analyzing/generating/completed/failed/cancelled
- Domain-specific: Gender, Season enums (fashion-only)
- MISSING: tenant_id, workspace_id (multi-tenancy)
- MISSING: design_mode (17-step pipeline mode indicator)

**Session** (`app/models/session.py`, 50 LOC):
- Fields: project_id, name, description, is_active
- MINIMAL compared to SPEC-01 DesignSession (9 states, current_step, etc.)
- MISSING: mode, status (state machine), current_step, brief_data, configuration

**DesignConcept** (`app/models/design.py`, 262 LOC):
- Fields: project_id, concept_name, concept_number, target_audience, season, silhouette, materials, color_palette, key_features, details, rationale, supporting_data, source_ids, feasibility/market/innovation scores, is_selected
- Fashion-specific fields (season, silhouette, materials) → validates DomainPack approach

**GenerationJob** (`app/models/generation.py`, 424 LOC):
- GenerationStatus: pending/queued/generating/completed/failed/cancelled
- ImageAsset: generation_job_id, file_name/path/url, image_type, dimensions, quality scores
- PatternDraft: fashion-specific (size_standard, measurements, front/back pattern)

### Service Layer (16 files)

| File | LOC | SPEC Relevance |
|------|-----|----------------|
| blueprint_service.py | 1,108 | EXCEEDS 1000 LOC limit |
| analysis_service.py | 963 | Near limit, trend analysis |
| prompt_service.py | 633 | Prompt engineering |
| image_generation_service.py | 619 | Directly maps to SPEC-03/04 |
| data_processor.py | 442 | Data pipeline |
| pipeline_utils.py | 426 | Pipeline orchestration helpers |
| consistency_pipeline.py | 405 | Quality pipeline |
| pipeline_orchestrator.py | ? | Maps to SPEC-01 state machine |
| full_workflow_service.py | ? | Full pipeline orchestration |
| pipeline_generation_steps.py | ? | Generation step handlers |
| pipeline_crawl_utils.py | ? | Crawling utilities |

### API Layer (22 files)

FastAPI-based API routes. All need port migration to 14000-series table per SPEC-01.

### Infrastructure

- **Port**: Single port (current FastAPI) → 14000 (user) + 14001 (admin) + 14002-14010 (services)
- **Async**: No Celery currently → SPEC requires Celery + Redis
- **Storage**: Local filesystem → SPEC requires MinIO/S3
- **Config**: `app/core/config.py` (235 LOC) with Pydantic settings → Django settings module

## State Machine Gap Analysis

### Current Project States (7)
draft → active → analyzing → generating → completed / failed / cancelled

### SPEC-01 DesignSession States (9)
queued → researching → concepting → referencing → abstracting → generating → documenting → review_ready / failed

### Gap
- Current states are project-level, SPEC states are session-level
- Step 15 (comparison/comparative analysis) has no explicit state
- Pipeline progress tracked by percentage, not by step number
- Need 17-step → 9-state explicit mapping table

## Multi-Tenancy Gap

Current system:
- No Tenant entity
- No Workspace entity
- No Membership entity
- No tenant_id on any data row
- User-Project direct ownership (owner_id FK)

SPEC-01 requires:
- Tenant entity with plan/is_active
- Workspace entity with tenant_id FK
- Membership entity (user-workspace-role)
- tenant_id/workspace_id on ALL data rows
- Tenant isolation in all queries

## Migration Path (High Level)

1. **Phase 1a**: SQLAlchemy → Django ORM model-by-model rewrite
2. **Phase 1b**: SQLite → PostgreSQL with data migration scripts
3. **Phase 1c**: Multi-tenancy injection (Tenant/Workspace/Membership + tenant_id on all tables)
4. **Phase 1d**: FastAPI → Django URL routing (or keep FastAPI with Django ORM hybrid)
5. **Phase 1e**: Add Celery + Redis for async task management
6. **Phase 1f**: Port migration to 14000-series table

## API Keys & Provider Status (CORRECTED)

Previous analysis incorrectly stated some API keys were empty. ALL keys are configured in .env:

| Provider | Key | Status |
|----------|-----|--------|
| Google Gemini | GEMINI_API_KEYS | Configured |
| ByteDance Seedream | BYTEDANCE_SEEDREAM_API_KEY | Configured |
| OpenAI | OPENAI_API_KEY | Configured |
| Alibaba/Qwen | ALIBABA_API_KEY | Configured |
| DeepSeek | DEEPSEEK_API_KEY | Configured |
| Xiaomi MiMo | XIAOMI_MIMO_API_KEY | Configured |
| MiniMax | MINIMAX_API_KEY | Configured |
| Kimi/Moonshot | KIMI_API_KEY | Configured |
| Pexels | PEXELS_API_KEY | Configured |
| Pixabay | PIXABAY_API_KEY | Configured |
| Unsplash | UNSPLASH_ACCESS_KEY | Configured |
| KIPRIS | KIPRIS_API_KEY | Configured |
| YouTube | YOUTUBE_API_KEYS | Configured (2 keys) |

This means image generation fallback chain (seedream→z-image→gemini→gpt-image-2) can be fully implemented. Image provider adapters (Unsplash/Pexels/Pixabay) also have keys ready.

## .env Additional Infrastructure

- Web Search Crawler API: `http://119.207.232.98:9123` (supports google, bing, duckduckgo, yahoo)
- Etoland crawler credentials configured
- Detailed model comparison table with 30+ models across 8 providers (pricing, speed, performance)
- Image generation model pricing: seedream ($0.04/img), z-image-turbo ($0.015-0.03/img)

## Key Files Requiring Attention

| File | Issue | Action |
|------|-------|--------|
| `app/models/base.py` | SQLAlchemy Base → Django Model | Full rewrite |
| `app/core/database.py` | SQLAlchemy engine → Django ORM | Full rewrite |
| `app/models/user.py` | Missing Tenant/Workspace | Add multi-tenancy |
| `app/models/session.py` | Minimal vs SPEC DesignSession | Full rewrite |
| `app/models/project.py` | Missing tenant_id, fashion-specific | Generalize + multi-tenant |
| `app/services/blueprint_service.py` | 1108 LOC (exceeds 1000) | Split into modules |
| `app/services/analysis_service.py` | 963 LOC (near limit) | Monitor during refactor |
| `app/core/config.py` | Pydantic settings → Django settings | Full rewrite |

## Structure.md Compliance

Target: 14+1 modules under `apps/` with 4-layer pattern each.

Current: Flat `app/` structure (models/, services/, api/, core/).

Legacy mapping (62 rows in structure.md) covers all current files to new module locations.
