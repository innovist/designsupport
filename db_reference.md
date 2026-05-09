# DB Reference

This file records schema-affecting specification changes that must be reflected when implementation migrations are created.

## 2026-05-08 — SPEC-02 Tier 3 Direct Style Guard

### references.ReferenceAsset.direct_style_apply

**Source**: `apps/references/infrastructure/orm/models.py`

**Purpose**: Persist whether a reference can be directly used for style application in the UI and generation workflow.

**Field**:
- direct_style_apply: BooleanField (default=True, indexed)

**Behavior**:
- Pipeline-created Tier 3 references are stored with `direct_style_apply=False`.
- Workspace reference board disables direct style application when this flag is false.

**Migration**:
- `apps/references/infrastructure/orm/migrations/0003_referenceasset_direct_style_apply.py`

## 2026-05-08 — Rerun Artifact Supersession

### Artifact `is_superseded` flags

**Source**: `apps/design_sessions/infrastructure/artifact_supersession.py`

**Purpose**: Preserve historical artifacts when a session is rerun from a step while keeping workspace APIs focused on the current artifact set.

**Fields**:
- `references.ReferenceAsset.is_superseded`: BooleanField (default=False, indexed)
- `concepts.ConceptCandidateModel.is_superseded`: BooleanField (default=False, indexed)
- `abstraction.AbstractionRuleModel.is_superseded`: BooleanField (default=False, indexed)
- `abstraction.SketchPromptModel.is_superseded`: BooleanField (default=False, indexed)
- `generation.GenerationJobModel.is_superseded`: BooleanField (default=False, indexed)
- `generation.GeneratedDesignModel.is_superseded`: BooleanField (default=False, indexed)
- `specs.SpecDocumentModel.is_superseded`: BooleanField (default=False, indexed)

**Behavior**:
- `rerun_from_step` marks downstream artifacts as superseded instead of deleting them.
- Workspace board queries exclude superseded artifacts by default.
- Historical rows remain available for audit and future history views.

**Migrations**:
- `apps/references/infrastructure/orm/migrations/0002_referenceasset_is_superseded_and_more.py`
- `apps/concepts/infrastructure/orm/migrations/0004_conceptcandidatemodel_is_superseded_and_more.py`
- `apps/abstraction/infrastructure/orm/migrations/0003_abstractionrulemodel_is_superseded_and_more.py`
- `apps/generation/infrastructure/orm/migrations/0004_generateddesignmodel_is_superseded_and_more.py`
- `apps/specs/infrastructure/orm/migrations/0002_specdocumentmodel_is_superseded_and_more.py`

## 2026-05-08 — FR-13 Project Preferred Image Model

### design_projects.DesignProject.preferred_image_model

**Source**: `apps/design_projects/infrastructure/orm/models.py`

**Purpose**: Persist the user's selected image-capable model for project-level generation routing.

**Field**:
- preferred_image_model: CharField (max_length=255, null=True, blank=True)

**Behavior**:
- Stores a `model_catalog.ModelCatalog.id` value only after API validation confirms the model is active and image-capable.
- Empty value means the ImageGeneration feature policy fallback chain is used.
- During generation, a non-empty value is passed to the model router as the preferred first model; existing policy fallback models remain available after it.

**Migration**:
- `apps/design_projects/infrastructure/orm/migrations/0002_designproject_preferred_image_model_and_more.py`

## 2026-05-08 — Tenant API Key Persistence

### admin_console.TenantORM.settings.api_keys

**Source**: `config/api_v1_views.py`, `apps/model_catalog/infrastructure/api_key_resolver.py`

**Purpose**: Persist tenant-scoped provider API keys across server restarts without falling back to another tenant.

**Storage**:
- `settings["api_keys"][ENV_NAME] = "signed:<django-signed-value>"`

**Behavior**:
- The runtime resolver reads process environment first, then the active tenant's signed DB value.
- Comma-separated or list input values are normalized and rotated in process memory for provider key rotation.
- Existing plaintext values remain readable for backward compatibility and are replaced with signed values on the next settings save.

## 2026-05-08 — SPEC-01 Session Input Configuration

### design_sessions.DesignSession.input_config

**Source**: `apps/design_sessions/infrastructure/orm/models.py`

**Purpose**: Persist the user-selected session runtime inputs that affect pipeline execution and dashboard display.

**Field**:
- input_config: JSONField (default=dict, blank=True)

**Stored keys**:
- filters: User-selected filters such as gender, age, season, and category.
- crawler_config: User-selected crawler sources, date range, and provider limits.
- auto_start: Whether the user requested immediate analysis start after session creation.
- generate_images: Whether image generation should be requested by the pipeline.
- generate_blueprints: Whether blueprint generation should be requested by the pipeline.

**Migration**:
- `apps/design_sessions/infrastructure/orm/migrations/0003_designsession_input_config.py`

## 2026-05-08 — SPEC-04-MODEL-ADMIN Model Catalog

### model_catalog.ModelProvider

**Source**: `apps/model_catalog/infrastructure/orm/models.py`

**Purpose**: Provider configuration for AI services

**Fields**:
- id: CharField (primary key, max_length=255)
- name: CharField (unique, indexed, max_length=255)
- api_key_env: CharField (max_length=255) - Environment variable name for API key
- base_url: URLField (nullable, max_length=500)
- endpoint_path: CharField (nullable, max_length=255)
- auth_scheme: CharField (choices: Bearer/ApiKey/Basic/Custom, default=Bearer)
- active: BooleanField (default=True, indexed)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (name) - unique
- (name, active)
- (active)

**Seed Data**:
- bytedance: BYTEDANCE_SEEDREAM_API_KEY, base_url=https://ark.ap-southeast.bytepluses.com/api/v3
- alibaba: ALIBABA_API_KEY
- google: GEMINI_API_KEYS
- openai: OPENAI_API_KEY

### model_catalog.ModelCatalog

**Source**: `apps/model_catalog/infrastructure/orm/models.py`

**Purpose**: Model catalog entries for AI models

**Fields**:
- id: CharField (primary key, max_length=255)
- provider: ForeignKey → ModelProvider (PROTECT, indexed)
- model_name: CharField (indexed, max_length=255)
- type: CharField (choices: text/chat/vision/image/search/embedding/multimodal, indexed)
- context_limit: IntegerField (nullable)
- cost_estimate: DecimalField (nullable, max_digits=10, decimal_places=4)
- modalities: JSONField (default=list)
- active: BooleanField (default=True, indexed)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (provider, model_name) - unique
- (provider, active)
- (type, active)

**Seed Data**: 6 models across 4 providers

### model_catalog.FeatureModelPolicy

**Source**: `apps/model_catalog/infrastructure/orm/models.py`

**Purpose**: Feature-to-model mapping with fallback chains

**Fields**:
- id: CharField (primary key, max_length=255)
- feature_key: CharField (unique, indexed, max_length=255) - 9 fixed keys
- primary_model: ForeignKey → ModelCatalog (PROTECT, indexed)
- fallback_models: ManyToManyField → ModelCatalog
- parameters: JSONField (default=dict)
- max_cost_per_call: DecimalField (nullable, max_digits=10, decimal_places=4)
- max_tokens: IntegerField (nullable)
- version: IntegerField (default=1, indexed)
- active: BooleanField (default=True, indexed)
- reviewer: CharField (nullable, max_length=255)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (feature_key) - unique
- (feature_key, active)
- (version)

**9 Fixed Feature Keys**: TrendResearch, ConceptChat, UserSketchAnalysis, ReferenceAnalysis, Abstraction, SketchPrompt, ImageGeneration, SpecWriting, Verification

### model_catalog.PromptPolicy

**Source**: `apps/model_catalog/infrastructure/orm/models.py`

**Purpose**: Prompt template policies for features

**Fields**:
- id: CharField (primary key, max_length=255)
- feature_key: CharField (indexed, max_length=255)
- prompt_version: CharField (max_length=255)
- system_prompt: TextField
- user_template: TextField
- active: BooleanField (default=True, indexed)
- reviewer: CharField (nullable, max_length=255)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (feature_key, prompt_version) - unique
- (feature_key, active)

### model_catalog.ModelInvocation

**Source**: `apps/model_catalog/infrastructure/orm/models.py`

**Purpose**: Model invocation metrics and tracking

**Fields**:
- id: CharField (primary key, max_length=255)
- feature_key: CharField (indexed, max_length=255)
- tenant_id: CharField (indexed, max_length=255)
- workspace_id: UUIDField (indexed)
- session_id: UUIDField (nullable, indexed)
- model: ForeignKey → ModelCatalog (PROTECT, indexed)
- status: CharField (choices: pending/success/failure/timeout, indexed)
- tokens_in: IntegerField (nullable)
- tokens_out: IntegerField (nullable)
- cost_estimate: DecimalField (nullable, max_digits=10, decimal_places=4)
- latency_ms: IntegerField (nullable)
- error_code: CharField (nullable, max_length=255)
- error_summary: TextField (nullable)
- created_at: DateTimeField (auto_now_add=True, indexed)

**Indexes**:
- (feature_key, -created_at)
- (tenant_id, -created_at)
- (status, -created_at)

**Data Retention**: 30 days (configurable)

### model_catalog.PolicyChangeLog

**Source**: `apps/model_catalog/infrastructure/orm/models.py`

**Purpose**: Audit log for policy changes

**Fields**:
- id: CharField (primary key, max_length=255)
- target_type: CharField (indexed, max_length=255)
- target_id: CharField (indexed, max_length=255)
- version_from: IntegerField (nullable)
- version_to: IntegerField
- actor_id: CharField (indexed, max_length=255)
- reason: TextField
- created_at: DateTimeField (auto_now_add=True, indexed)

**Indexes**:
- (target_type, target_id, -created_at)
- (actor_id, -created_at)

**Data Retention**: 1 year (audit trail)

---

## 2026-05-08 — SPEC-01-FOUNDATION-SESSION Core Models

### accounts.User

**Source**: `apps/accounts/infrastructure/orm/models.py`

**Purpose**: Custom user model with email-based authentication

**Fields**:
- id: UUIDField (primary key)
- email: EmailField (unique, indexed, max_length=255)
- password_hash: CharField (max_length=255) - Argon2 hash
- display_name: CharField (max_length=100)
- default_workspace_id: UUIDField (nullable, indexed)
- is_active: BooleanField (default=True, indexed)
- is_tenant_admin: BooleanField (default=False)
- is_staff: BooleanField (default=False)
- created_at: DateTimeField (auto_now_add=True, inherited)
- updated_at: DateTimeField (auto_now=True, inherited)

**Indexes**:
- (email)
- (default_workspace_id)
- (is_active)
- (created_at)

**Manager**: UserManager with create_user(), create_superuser()

### workspaces.Tenant

**Source**: `apps/workspaces/infrastructure/orm/models.py`

**Purpose**: Root tenant entity for multi-tenancy

**Fields**:
- id: CharField (primary key, max_length=255)
- name: CharField (max_length=255)
- plan: CharField (choices: free/pro/enterprise, default=free)
- is_active: BooleanField (default=True, indexed)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (is_active)
- (plan)

**Manager**: TenantManager with get_active(), get_by_plan()

### workspaces.Workspace

**Source**: `apps/workspaces/infrastructure/orm/models.py`

**Purpose**: Workspace for organizing design projects within tenant

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel (self-reference)
- name: CharField (max_length=255)
- description: TextField (nullable)
- is_active: BooleanField (default=True, indexed)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (tenant_id, is_active)
- (workspace_id, is_active)
- (tenant_id, workspace_id) - inherited from TenantScopedModel

**Manager**: WorkspaceManager with for_tenant(), get_active()

### workspaces.Membership

**Source**: `apps/workspaces/infrastructure/orm/models.py`

**Purpose**: Many-to-many relationship between User and Workspace with roles

**Fields**:
- id: BigAutoField (primary key)
- user_id: UUIDField (indexed)
- workspace_id: UUIDField (indexed)
- role: CharField (choices: admin/lead/designer/viewer, default=viewer)
- joined_at: DateTimeField (auto_now_add=True)

**Constraints**:
- unique_together: (user_id, workspace_id)

**Indexes**:
- (user_id, workspace_id)
- (workspace_id, role)

**Manager**: MembershipManager with for_workspace(), for_user(), for_tenant()

### audit_logs.AuditLog

**Source**: `apps/audit_logs/infrastructure/orm/models.py`

**Purpose**: Audit trail for all domain operations

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel
- actor_id: UUIDField (indexed)
- action_type: CharField (max_length=100)
- target_type: CharField (max_length=100)
- target_id: UUIDField
- payload_digest: CharField (max_length=255)
- created_at: DateTimeField (auto_now_add=True, indexed)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (actor_id, created_at)
- (tenant_id, workspace_id, created_at)

### design_projects.DesignProject

**Source**: `apps/design_projects/infrastructure/orm/models.py`

**Purpose**: Organizes design sessions within workspaces

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - explicit for queries
- title: CharField (max_length=255)
- domain: CharField (choices: industrial/fashion/visual/advertising)
- status: CharField (choices: active/archived/deleted, default=active, indexed)
- owner_id: UUIDField (indexed)
- is_deleted: BooleanField (default=False, indexed) - inherited from SoftDeleteModel
- deleted_at: DateTimeField (nullable) - inherited from SoftDeleteModel
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (workspace_id, status)
- (owner_id)
- (domain)
- (is_deleted, -created_at) - inherited from SoftDeleteModel

**Manager**: DesignProjectManager with for_workspace(), active(), by_domain()

### design_sessions.DesignSession

**Source**: `apps/design_sessions/infrastructure/orm/models.py`

**Purpose**: Orchestrates 17-step design creation pipeline

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel
- project_id: UUIDField (indexed)
- mode: CharField (choices: guided/auto, default=guided)
- status: CharField (choices: 9 states, default=queued, indexed)
- current_step: IntegerField (default=1, range 1-17)
- version: IntegerField (default=1)
- started_by: UUIDField (indexed)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Status Choices**:
- queued: Initial state
- researching: Trend/market research (step 5)
- concepting: Concept generation (step 6)
- referencing: Reference search (step 9)
- abstracting: Reference/sketch analysis (step 11)
- generating: Sketch generation (step 13)
- documenting: Spec document (step 16)
- review_ready: Review/approval (step 17, terminal)
- failed: Error state

**Indexes**:
- (project_id, status)
- (tenant_id, workspace_id, status)
- (started_by)

**Manager**: DesignSessionManager with for_project(), active(), failed()

**Validation**: clean() method validates state transitions per SPEC-01 §5.3

### design_sessions.DesignBrief

**Source**: `apps/design_sessions/infrastructure/orm/models.py`

**Purpose**: Structured design requirements for a session

**Fields**:
- id: UUIDField (primary key)
- session_id: UUIDField (unique, indexed)
- purpose: TextField
- audience: TextField
- usage_context: TextField
- constraints: TextField
- result_form: TextField
- clarifying_questions: JSONField (default=list)
- score: FloatField (default=0.0)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (session_id) - unique

### design_sessions.DecisionLog

**Source**: `apps/design_sessions/infrastructure/orm/models.py`

**Purpose**: Records all decisions made during session execution

**Fields**:
- id: UUIDField (primary key)
- session_id: UUIDField (indexed)
- step: IntegerField (range 1-17)
- action: CharField (max_length=255)
- actor_kind: CharField (choices: user/auto)
- actor_id: UUIDField
- rationale: TextField
- evidence_refs: JSONField (default=list)
- created_at: DateTimeField (auto_now_add=True, indexed)

**Indexes**:
- (session_id, created_at)
- (actor_id, created_at)

**Manager**: DecisionLogManager with for_session(), by_actor()

### conversations.Conversation

**Source**: `apps/conversations/infrastructure/orm/models.py`

**Purpose**: Chat conversation for a design session

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel
- session_id: UUIDField (indexed)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (session_id)
- (tenant_id, workspace_id, session_id)

### conversations.ChatMessage

**Source**: `apps/conversations/infrastructure/orm/models.py`

**Purpose**: Individual messages in a conversation

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel
- conversation_id: UUIDField (indexed)
- role: CharField (choices: user/assistant/system)
- content: TextField
- evidence_refs: JSONField (default=list)
- is_hypothesis: BooleanField (default=False)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (conversation_id, created_at)
- (tenant_id, workspace_id)

### user_assets.UserSketchAsset

**Source**: `apps/user_assets/infrastructure/orm/models.py`

**Purpose**: User-uploaded sketch assets

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel
- session_id: UUIDField (indexed)
- uploader_id: UUIDField
- original_uri: TextField
- sha256: CharField (max_length=64, indexed)
- mime_type: CharField (max_length=100)
- size: IntegerField
- version: IntegerField (default=1)
- parent_asset_id: UUIDField (nullable)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (session_id)
- (sha256)
- (tenant_id, workspace_id)

### user_assets.SketchAnalysis

**Source**: `apps/user_assets/infrastructure/orm/models.py`

**Purpose**: AI analysis of user sketches

**Fields**:
- id: UUIDField (primary key)
- tenant_id: CharField (indexed) - inherited from TenantScopedModel
- workspace_id: UUIDField (indexed) - inherited from TenantScopedModel
- sketch_id: UUIDField (indexed, foreign key to UserSketchAsset)
- intent: TextField
- form_notes: TextField
- structure_notes: TextField
- unclear_points: JSONField (default=list)
- keep_elements: JSONField (default=list)
- vary_elements: JSONField (default=list)
- status: CharField (choices: hypothesis/confirmed/rejected)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (sketch_id)
- (tenant_id, workspace_id)

## 2026-05-07 — SPEC document review additions

### ModelProvider

Source: `.moai/specs/SPEC-04-MODEL-ADMIN/spec.md`

- Add `endpoint_path`: provider endpoint suffix such as `/images/generations`. Required for providers whose base URL already includes version path segments.
- Add `auth_scheme`: authentication scheme such as `Bearer`.
- Validation: `base_url + endpoint_path` must not duplicate API version segments such as `/api/v3/api/v3`.

### PromptPattern

Source: `.moai/specs/SPEC-03-CREATION/spec.md`

- New entity: `PromptPattern(id, name, category, source_reference, input_slots, output_constraints, safety_rules, domain_tags[], active)`.
- Purpose: store curated image-generation prompt pattern metadata derived from reference sources such as `PicoTrex/Awesome-Nano-Banana-images`.
- Constraint: store source metadata and structured slots, not verbatim external runtime prompts unless license/source review explicitly approves it.

### PromptSafetyViolation

Source: `.moai/specs/SPEC-03-CREATION/spec.md`

- New entity: `PromptSafetyViolation(id, session_id, prompt_id?, reason, source_refs[], created_at)`.
- Purpose: record rejected prompt generation attempts, including direct artist/brand/work imitation, unsafe license usage, or direct style application from high-risk references.

---

## 2026-05-08 — SPEC-02-TREND-KNOWLEDGE Trend Knowledge App

### trend_knowledge.TrendSource

**Source**: `apps/trend_knowledge/infrastructure/orm/models.py`

**Purpose**: Sources for trend crawling (websites, APIs, feeds)

**Fields**:
- id: UUIDField (primary key)
- name: CharField (indexed, max_length=255)
- url: URLField (max_length=2048)
- domain: CharField (indexed, max_length=100) - Domain category (industrial, fashion, visual, advertising)
- crawl_schedule: CharField (max_length=100) - Cron expression for crawling schedule
- trust_level: CharField (max_length=20) - Source trust rating (low, medium, high)
- license: CharField (max_length=100) - License type for content
- active: BooleanField (default=True, indexed)
- created_at: DateTimeField (auto_now_add=True, inherited)
- updated_at: DateTimeField (auto_now=True, inherited)

**Indexes**:
- (domain, active)
- (active)

**Manager**: Django ORM default manager

### trend_knowledge.TrendDocument

**Source**: `apps/trend_knowledge/infrastructure/orm/models.py`

**Purpose**: Collected documents from trend sources

**Fields**:
- id: UUIDField (primary key)
- source_id: UUIDField (indexed) - Reference to TrendSource
- title: CharField (max_length=500)
- url: URLField (max_length=2048)
- published_at: DateTimeField (indexed) - Original publication date
- collected_at: DateTimeField (indexed) - Collection timestamp
- raw_uri: CharField (max_length=2048) - Storage URI for raw file
- parsed_text_uri: CharField (max_length=2048, nullable) - Storage URI for parsed text
- hash: CharField (indexed, max_length=64) - SHA-256 for deduplication
- parse_status: CharField (indexed, choices: pending/parsing/parsed/failed)
- created_at: DateTimeField (auto_now_add=True, inherited)
- updated_at: DateTimeField (auto_now=True, inherited)

**Indexes**:
- (source_id, collected_at)
- (parse_status)
- (hash)

**Manager**: Django ORM default manager

### trend_knowledge.TrendInsight

**Source**: `apps/trend_knowledge/infrastructure/orm/models.py`

**Purpose**: Extracted insights from trend documents with evidence

**Fields**:
- id: UUIDField (primary key)
- document_id: UUIDField (indexed) - Reference to TrendDocument
- summary: TextField - Insight summary text
- keywords: JSONField (default=list) - Extracted keywords
- domain_tags: JSONField (default=list) - Domain classification tags
- evidence_quote: TextField - Direct quote for citation
- confidence: FloatField - Confidence score (0.0 to 1.0)
- recency_score: FloatField - Recency score (0.0 to 1.0)
- created_at: DateTimeField (auto_now_add=True, inherited)

**Indexes**:
- (document_id)
- (domain_tags)

**Manager**: Django ORM default manager

### trend_knowledge.TrendTaxonomy

**Source**: `apps/trend_knowledge/infrastructure/orm/models.py`

**Purpose**: Data-driven taxonomy for categorizing trends (NO hardcoded categories)

**Fields**:
- id: UUIDField (primary key)
- domain: CharField (indexed, max_length=100) - Domain category
- category: CharField (indexed, max_length=100) - Category name
- label: CharField (max_length=255) - Human-readable label
- description: TextField (blank=True) - Category description
- parent_id: UUIDField (indexed, nullable) - Parent category ID for hierarchy
- active: BooleanField (default=True, indexed)
- created_at: DateTimeField (auto_now_add=True, inherited)
- updated_at: DateTimeField (auto_now=True, inherited)

**Indexes**:
- (domain, active)
- (category)
- (parent_id)

**Seed Data**: 7 initial categories per domain (Nature, Product, Architecture, Fashion, Graphic, Advertising, Material) for 4 domains (28 total)

**Manager**: Django ORM default manager

### trend_knowledge.ParsingFailureQueue

**Source**: `apps/trend_knowledge/infrastructure/orm/models.py`

**Purpose**: Tracks failed documents for admin review and retry

**Fields**:
- id: UUIDField (primary key)
- document_id: UUIDField (indexed, unique) - Reference to failed TrendDocument
- reason: TextField - Failure reason
- retried_count: IntegerField (default=0) - Number of retry attempts
- created_at: DateTimeField (auto_now_add=True, inherited)

**Indexes**:
- (document_id) - unique
- (-created_at) - for sorting newest first

**Manager**: Django ORM default manager

---

## 2026-05-08 — SPEC-04-ADMIN-CONSOLE Admin Console

### admin_console.AdminSession

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Purpose**: Admin session management for authentication and authorization

**Fields**:
- id: UUIDField (primary key)
- user_id: UUIDField (indexed)
- role: CharField (choices: super_admin/tenant_admin/viewer, default=viewer)
- tenant_id: CharField (nullable, indexed, max_length=255)
- expires_at: DateTimeField (nullable, indexed)
- is_active: BooleanField (default=True, indexed)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (user_id, is_active)
- (tenant_id, is_active)
- (user_id)
- (tenant_id)
- (expires_at)
- (is_active)

**Methods**: to_domain() - converts to domain entity

### admin_console.PolicyChangeLog

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Purpose**: Audit log for policy changes with version tracking

**Fields**:
- id: UUIDField (primary key)
- policy_id: CharField (indexed, max_length=255)
- policy_type: CharField (choices: feature/prompt, default=feature)
- version: IntegerField (indexed)
- changed_by: UUIDField (indexed)
- change_type: CharField (choices: create/update/rollback/deactivate, default=create)
- previous_version: IntegerField (nullable)
- change_summary: TextField
- change_details: JSONField (default=dict)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (policy_id, -version)
- (policy_type, -created_at)
- (changed_by, -created_at)
- (policy_id)
- (version)
- (changed_by)

**Methods**: to_domain() - converts to domain entity

### admin_console.AdminMetrics

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Purpose**: Cached metrics summaries for admin dashboard

**Fields**:
- id: UUIDField (primary key)
- period: CharField (choices: daily/weekly/monthly, indexed)
- start_date: DateTimeField (indexed)
- end_date: DateTimeField (indexed)
- feature_key: CharField (nullable, indexed, max_length=100)
- total_cost: DecimalField (max_digits=12, decimal_places=4, default=0.0)
- cost_by_feature: JSONField (default=dict)
- total_tokens: BigIntegerField (default=0)
- tokens_by_feature: JSONField (default=dict)
- prompt_tokens: BigIntegerField (default=0)
- completion_tokens: BigIntegerField (default=0)
- total_invocations: IntegerField (default=0)
- invocations_by_feature: JSONField (default=dict)
- successful_invocations: IntegerField (default=0)
- failed_invocations: IntegerField (default=0)
- failure_rate: FloatField (default=0.0)
- failure_reasons: JSONField (default=dict)
- created_at: DateTimeField (auto_now_add=True, indexed)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (period, -start_date)
- (feature_key, period, -start_date)
- (-created_at)
- (period)
- (start_date)
- (end_date)
- (feature_key)

### admin_console.FeaturePolicy

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Purpose**: Feature-to-model mapping policies with versioning

**Fields**:
- id: UUIDField (primary key)
- feature_key: CharField (unique, indexed, max_length=100)
- version: IntegerField (default=1, indexed)
- is_active: BooleanField (default=True, indexed)
- model_type: CharField (max_length=50)
- primary_model: CharField (max_length=255)
- fallback_models: JSONField (default=list)
- max_retries: IntegerField (default=3)
- timeout_seconds: IntegerField (default=30)
- max_cost_per_request: DecimalField (max_digits=10, scale=4)
- max_cost_per_day: DecimalField (max_digits=12, scale=4)
- max_cost_per_month: DecimalField (max_digits=14, scale=4)
- currency: CharField (max_length=3, default=USD)
- required_model_types: JSONField (default=list)
- min_context_length: IntegerField (default=4096)
- supports_streaming: BooleanField (default=False)
- supports_function_calling: BooleanField (default=False)
- max_tokens_per_request: IntegerField (default=4096)
- created_by: UUIDField (indexed)
- modified_by: UUIDField (indexed)
- change_reason: TextField (blank=True)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (feature_key, -version)
- (is_active, feature_key)
- (feature_key) - unique
- (version)
- (is_active)

**Constraints**:
- unique_together: (feature_key)

### admin_console.PromptPolicy

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Purpose**: Prompt template policies for features with versioning

**Fields**:
- id: UUIDField (primary key)
- feature_key: CharField (unique, indexed, max_length=100)
- version: IntegerField (default=1, indexed)
- is_active: BooleanField (default=True, indexed)
- system_prompt: TextField
- user_template: TextField
- temperature: FloatField (default=0.7)
- max_tokens: IntegerField (default=2048)
- top_p: FloatField (default=0.9)
- frequency_penalty: FloatField (default=0.0)
- presence_penalty: FloatField (default=0.0)
- created_by: UUIDField (indexed)
- modified_by: UUIDField (indexed)
- change_reason: TextField (blank=True)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (feature_key, -version)
- (is_active, feature_key)
- (feature_key) - unique
- (version)
- (is_active)

**Constraints**:
- unique_together: (feature_key)

### admin_console.Tenant

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Purpose**: Tenant management for multi-tenancy

**Fields**:
- id: CharField (primary key, max_length=255)
- name: CharField (max_length=255)
- display_name: CharField (max_length=255)
- is_active: BooleanField (default=True, indexed)
- plan: CharField (choices: free/pro/enterprise, default=free)
- max_users: IntegerField (default=5)
- max_projects: IntegerField (default=10)
- max_storage_gb: IntegerField (default=10)
- created_by: UUIDField
- settings: JSONField (default=dict)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (is_active, plan)
- (-created_at)
- (is_active)

### admin_console.UserTenantRole

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Purpose**: User-tenant-role associations for access control

**Fields**:
- id: UUIDField (primary key)
- user_id: UUIDField (indexed)
- tenant_id: CharField (indexed, max_length=255)
- role: CharField (choices: owner/admin/member/viewer, default=member)
- is_active: BooleanField (default=True)
- created_at: DateTimeField (auto_now_add=True)
- updated_at: DateTimeField (auto_now=True)

**Indexes**:
- (tenant_id, role)
- (user_id, is_active)
- (user_id)
- (tenant_id)

**Constraints**:
- unique_together: (user_id, tenant_id)

---

## 2026-05-08 — SPEC-03-CREATION Concepts

### concepts.ConceptCandidate

**Source**: `apps/concepts/infrastructure/orm/models.py`

**Purpose**: Concept candidates for design exploration

**Fields**:
- id: UUIDField (primary key)
- session_id: UUIDField (indexed)
- title: CharField (max_length=500)
- description: TextField
- rationale: TextField
- rationale_refs: JSONField (default=list) - List of UUIDs referencing TrendInsight or ReferenceAnalysis
- risks: JSONField (default=list) - List of risk strings *(added 2026-05-08)*
- domain_tags: JSONField (default=list)
- status: CharField (choices: draft/proposed/adopted/discarded, default=draft)
- score: FloatField (nullable)
- novelty: FloatField (nullable)
- fit_score: FloatField (nullable)
- created_by: UUIDField
- created_at: DateTimeField (auto_now_add=True, inherited)
- updated_at: DateTimeField (auto_now=True, inherited)

**Indexes**:
- (session_id)
- (status)
- (created_at)

**Migration**: `apps/concepts/infrastructure/orm/migrations/0002_add_risks.py`

### concepts.ConceptDecision

**Source**: `apps/concepts/infrastructure/orm/models.py`

**Purpose**: Decision records for concept candidates

**Fields**:
- id: UUIDField (primary key)
- concept_id: UUIDField (indexed)
- decision: CharField (choices: adopt/hold/discard/explore_more)
- actor_kind: CharField (choices: user/auto)
- actor_id: UUIDField
- rationale: TextField
- evidence_refs: JSONField (default=list) - List of UUIDs
- created_at: DateTimeField (auto_now_add=True, inherited)

**Indexes**:
- (concept_id)
- (created_at)

---

## 2026-05-08 — Django ORM Migration Alignment and Runtime Onboarding

### Migration routing

**Source**: `config/settings/base.py`

**Change**: Django app migrations are routed to each module's `apps/<module>/infrastructure/orm/migrations` package through `MIGRATION_MODULES`.

**Reason**: The modular architecture stores ORM models under each bounded context's infrastructure layer. This keeps Django migration discovery aligned with the existing module structure.

### accounts.User

**Source**: `apps/accounts/infrastructure/orm/models.py`

**Required/default behavior**:
- `id`: UUID primary key now has `default=uuid4` and `editable=False` in model and migration.
- `password_hash`: remains required.
- `display_name`: remains required.
- `default_workspace_id`: nullable; filled automatically during onboarding when a default workspace is created.

**Migration**: `apps/accounts/infrastructure/orm/migrations/0001_initial.py`

### workspaces.Tenant / workspaces.Workspace / workspaces.Membership

**Source**: `apps/workspaces/infrastructure/orm/models.py`, `apps/workspaces/infrastructure/signals.py`

**Runtime behavior**:
- New users receive a real `Tenant`, `Workspace`, and admin `Membership` through the workspace onboarding signal.
- `Workspace.id` and tenant-scoped `Workspace.workspace_id` are set to the same UUID for the workspace root row.
- No mock/default placeholder tenant is used; tenant and workspace IDs are generated per user.

**Migration**: `apps/workspaces/infrastructure/orm/migrations/0001_initial.py`

### Runtime API-backed tables

The workspace board API now reads persisted rows from:
- `conversations`, `chat_messages`
- `user_sketch_assets`, `sketch_analyses`
- `references_asset`, `references_analysis`
- `abstraction_rules`
- `concept_candidates`, `concept_decisions`
- `generation_jobs`, `generated_designs`
- `spec_documents`

No new DB fields were added for these runtime API endpoints.

---

## 2026-05-08 — SPEC-06 Admin Console Policy Versioning

### admin_console.FeaturePolicyORM / admin_console.PromptPolicyORM

**Source**: `apps/admin_console/infrastructure/orm/models.py`

**Change**:
- `feature_key` is no longer globally unique.
- `(feature_key, version)` is now unique.

**Reason**: SPEC-06 policy editing creates a new immutable version for each save while keeping only one active policy per feature. A single `feature_key` unique constraint prevented version history from being stored.

**Migration**: `apps/admin_console/infrastructure/orm/migrations/0002_alter_featurepolicyorm_feature_key_and_more.py`

### model_catalog.FeatureModelPolicyModel

**Source**: `apps/model_catalog/infrastructure/orm/models.py`

**Change**:
- `feature_key` is no longer globally unique.
- `(feature_key, version)` is now unique.

**Reason**: Admin console policy changes must be reflected in the runtime model router. The router reads `feature_model_policies`, so this table also needs version history support with one active policy per feature.

**Migration**: `apps/model_catalog/infrastructure/orm/migrations/0003_alter_featuremodelpolicymodel_feature_key_and_more.py`

---

## 2026-05-09 — FastAPI Design Tool Initial Schema Alignment

### trend_insight

**Source**: `app/models/trends.py`

**Change**:
- Added nullable `session_id` foreign key to `design_session.id`.

**Reason**: Trend insights are generated from a specific design session search. Without `session_id`, concept generation and spec documents could mix trend evidence from unrelated sessions, violating the evidence-based pipeline contract.

**Migration**: `alembic/versions/482a29aee870_initial_schema.py`

### feature_model_setting

**Source**: `app/models/workspace.py`, `app/infrastructure/repositories/workspace_repository.py`

**Required/default behavior**:
- Default workspace initialization now creates one `FeatureModelSetting` row for each canonical feature key:
  `abstraction`, `sketch_analysis`, `concept_generation`, `chat`, `image_generation`, `reference_analysis`, `brief_structuring`, `spec_writing`, `trend_analysis`.
- Provider/model defaults are editable in the user workspace settings page.
- API key values remain `.env`-only and are not stored in this table.

**Reason**: Runtime AI routes must resolve feature-specific models consistently and must fail clearly when provider API keys are missing.

**Migration**: `alembic/versions/482a29aee870_initial_schema.py`
