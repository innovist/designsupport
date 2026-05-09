# Research: SPEC-03-CREATION

Codebase analysis for creation pipeline, concept generation, abstraction, and image generation.

## Current Creation System

### Concept Generation

**Existing model: DesignConcept** (`app/models/design.py`):
- Fashion-specific fields: season, silhouette, materials, color_palette
- Scoring: feasibility_score, market_potential, innovation_score
- Rationale tracking: rationale, supporting_data, source_ids

**SPEC-03 ConceptCandidate requirements:**
- rationale_refs enforcement (INV-03-01: evidence-based concepts must reference specific trend/research data)
- Domain-agnostic concept structure (no season/silhouette in core model)
- DomainPack templates for domain-specific fields

**Gap:** Current DesignConcept is fashion-only. SPEC requires domain-agnostic concept model with DomainPack-driven specialization.

### Prompt Engineering

**Existing model: PromptSpec** (`app/models/design.py`, 262 LOC):
- prompt_type: garment, model_fitting, blueprint
- base_prompt, optimized_prompt, negative_prompt
- Parameters: width, height, steps, cfg_scale, seed
- Reference: reference_image_url, reference_strength, controlnet_type

**SPEC-03 SketchPrompt requirements:**
- preserve_original vs expand_concept modes
- parent_sketch_id preservation (INV-03-02)
- User sketch originals are immutable

**Gap:** Current PromptSpec has no sketch preservation logic. SPEC-03 separates refinement from variation generation.

### Abstraction Engine

**Current state:**
- No 6-axis abstraction system
- No abstraction model in database
- `app/services/analysis_service.py` (963 LOC) has analysis but not SPEC-03 abstraction

**SPEC-03 6-axis abstraction:**
1. form (형태)
2. structure (구조)
3. surface (표면)
4. color_material (색상/소재)
5. meaning (의미)
6. usability (사용성)

Each axis has domain-specific templates in DomainPack.

### Image Generation

**Current implementation** (`app/services/image_generation_service.py`, 619 LOC):
- Uses `IMAGE_GEN_PROVIDER=nano_banana` with `gemini-2.5-flash-image` model
- `.env` shows: GEMINI_API_KEYS set, BYTEDANCE_SEEDREAM_API_KEY/OPENAI_API_KEY/ALIBABA_API_KEY all empty
- GenerationJob model with status tracking
- ImageAsset model with quality scoring

**SPEC-03/04 image generation chain:**
Primary: `bytedance/seedream-4.5` (BytePlus Ark API, Bearer auth)
Fallback 1: `alibaba/z-image-turbo`
Fallback 2: `google/gemini-3.1-flash-image-preview` (nanobanana2)
Fallback 3: `openai/gpt-image-2`

**API Keys Status (CORRECTED):** ALL image generation provider keys are configured in .env:
- `BYTEDANCE_SEEDREAM_API_KEY=a79b284f-...` (NOT empty)
- `ALIBABA_API_KEY=sk-e1f87...` (NOT empty)
- `OPENAI_API_KEY=sk-proj-...` (NOT empty)
- `GEMINI_API_KEYS=AIzaSyBq...` (configured)

**Gap:**
- Current uses nano_banana/gemini as primary, SPEC requires seedream-4.5
- No fallback chain implemented (but all provider keys ARE available)
- Need ModelRouter integration (SPEC-04) for provider selection

**Image Generation Endpoint Details (from .env):**
- seedream-4-5-251128: `POST https://ark.ap-southeast.bytepluses.com/api/v3/images/generations` (Bearer auth)
- z-image-turbo: `POST https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation` (Bearer auth)
- gemini-2.5-flash-image: via google-generativeai SDK
- gpt-image-2: `POST https://api.openai.com/v1/images/generations` (Bearer auth)

### GenerationJob State Machine

**Current states (6):** pending → queued → generating → completed / failed / cancelled

**SPEC-03 requirements:**
- Integration with DesignSession state machine (9 states in SPEC-01)
- Generation job tracks model_used, fallback chain position
- quality/consistency scores for generated images

### DomainPack System

**Current state:**
- Fashion-specific hardcoded in DesignConcept (season, silhouette, materials)
- No domain pack abstraction
- No manifest.yaml configuration

**SPEC-03 DomainPack requirements:**
- Data-driven domain specialization
- No code branching (INV-03-03)
- Templates for concept, abstraction, prompt, spec
- Domain seed mappings in `domain_packs/<domain>/manifest.yaml`

**Target domains:** industrial, fashion, visual, advertising (extensible)

### SpecDocument Builder

**Current state:**
- `app/models/report.py` exists but fashion-specific
- No structured spec document builder

**SPEC-03 SpecDocument requirements:**
- Required sections: concept_summary, abstraction_analysis, design_rationale, reference_catalog, generation_log, iteration_history
- Builder pattern for section-by-section construction
- Version tracking with design_iteration

## Key Gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| Fashion-only concepts | CRITICAL | Must generalize with DomainPack |
| No abstraction engine | CRITICAL | 6-axis system is entirely new |
| Image gen provider mismatch | HIGH | nano_banana → seedream-4.5 primary (keys ARE available) |
| No fallback chain | HIGH | Single provider → 4-provider chain (all keys configured) |
| No sketch preservation | HIGH | preserve_original/expand_concept missing |
| No DomainPack | HIGH | Data-driven domain specialization needed |
| No SpecDocument builder | MEDIUM | Structured document generation |
| No prompt pattern library | MEDIUM | Need curated PromptPattern seeds from external examples without copying runtime text |

## Prompt Pattern Reference: Awesome-Nano-Banana-images

Reference: https://github.com/PicoTrex/Awesome-Nano-Banana-images

The repository is a curated gallery of Nano Banana / Nano Banana Pro image generation and editing examples with prompts. It also references a Nano-consistent-150k dataset focused on identity-consistent image editing scenarios. The repository is useful for prompt structure research, but production prompts must not copy external example text verbatim or hardcode a specific creator/brand/work style.

Applicable prompt pattern families for this product:

| Pattern family | Product use |
|---|---|
| line_to_render | User sketch refinement and visual cleanup |
| multi_reference_fusion | Combining user sketch, safe references, and abstraction rules |
| product_packaging | Industrial/visual/advertising domain application |
| material_texture | Surface/material exploration from abstraction rules |
| exploded_view | Industrial design structure explanation |
| storyboard | Advertising campaign and visual narrative variants |
| moodboard_collage | Fashion/visual direction boards |
| diagram/annotation | SpecDocument visual explanation and decision rationale |
| domain_application | Applying concept to product/look/poster/campaign cut |
| refinement_preserve_original | Preserving user sketch intent while improving fidelity |

Implementation instruction:
- Convert external examples into `PromptPattern` metadata: category, required input slots, output constraints, safety rules, and domain tags.
- Runtime prompts must be generated from `DesignBrief`, `SketchAnalysis`, `ReferenceAnalysis`, `AbstractionRule`, `DomainPack`, and SPEC-04 `PromptPolicy`.
- Do not store external prompt text as active runtime templates unless license/source review explicitly approves it.
- Any pattern that asks for direct imitation of a specific artist, brand, character, or copyrighted work must be blocked by `PromptSafetyViolation`.

## Entity Mapping: Current → SPEC

| Current Entity | SPEC-03 Entity | Migration |
|---------------|----------------|-----------|
| DesignConcept | ConceptCandidate | Generalize + DomainPack |
| PromptSpec | SketchPrompt | Add sketch preservation modes |
| GenerationJob | GenerationJob (enhanced) | Add fallback tracking |
| ImageAsset | ImageAsset (enhanced) | Add generation context |
| (none) | AbstractionResult | New (6-axis) |
| (none) | SpecDocument | New |
| (none) | DesignIteration | New |
| PatternDraft | (deferred) | Phase 2 concern |
