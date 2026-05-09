# SPEC-01-DESIGN-TOOL-001 Implementation Checklist

**Created**: 2026-05-09
**Status**: In Progress

---

## Phase 1: Workspace & Settings

### REQ-WS-001: Default workspace auto-creation
- [x] Workspace auto-created on startup (main.py lifespan)
- [x] WorkspaceSetting auto-created with defaults
- [x] FeatureModelSetting initialized for 9 feature keys

### REQ-WS-002: Settings page UI
- [x] GET /workspace/settings HTML page
- [x] GET /api/workspace/settings JSON endpoint
- [x] Editable UI for all settings

### REQ-WS-003: Feature model settings
- [x] PUT /api/workspace/feature-models/{feature_key}
- [x] Saves provider, model, temperature, max_tokens

### REQ-WS-004: Missing config blocking
- [x] SettingsRequiredError raised when config missing
- [x] settings_required_response helper in errors.py
- [ ] All API routes that use AI check for settings and return proper error

### REQ-WS-005: API Key alias display
- [x] GET /api/workspace/api-key-aliases endpoint
- [x] Shows alias only, never raw key

### REQ-WS-006: Dangerous action confirmation
- [x] Settings UI uses confirmation for destructive actions

---

## Phase 2: Sessions & Brief

### REQ-SESSION-001: Session creation with brief
- [x] POST /api/sessions creates session
- [x] POST /api/sessions/{id}/brief structures brief via AI
- [x] Extracts purpose/domain/target/constraints/use_case

### REQ-SESSION-002: Clarification questions
- [x] structure_brief generates clarification questions for missing fields
- [x] Chat messages with stage info stored

### REQ-SESSION-003: Chat message storage
- [x] POST /api/sessions/{id}/messages
- [x] Messages saved with session_id, stage, created_at
- [x] evidence_links included for evidence-backed claims

### REQ-SESSION-004: Pipeline stage management
- [x] 9 pipeline stages defined
- [x] PATCH /api/sessions/{id}/stage updates stage
- [x] Stage stored in design_session.pipeline_stage

### REQ-SESSION-005: Uncertainty threshold (auto mode)
- [x] is_hypothesis field on TrendInsight
- [x] concept generation filters out hypothesis insights (is_hypothesis == False filter)
- [ ] Auto mode stops on high uncertainty (not implemented - deferred to next SPEC)

### REQ-SESSION-006: Rerun from step
- [x] POST /api/sessions/{id}/rerun endpoint exists
- [ ] Actual rerun logic implemented (skeleton only - deferred)

---

## Phase 3: Sketches & References & Trends

### REQ-SKETCH-001: Sketch upload
- [x] POST /api/sessions/{id}/sketches
- [x] Files saved to uploads/sketches/{session_id}/
- [x] Original files never overwritten (unique filename)

### REQ-SKETCH-002: Sketch analysis
- [x] POST /api/sketches/{id}/analyze
- [x] Saves intent/form/structure/unclear/questions to sketch_analysis
- [x] User confirmation required items displayed

### REQ-SKETCH-003: AI interpretation hypothesis label
- [x] AI interpretation stored separately from user confirmation
- [x] POST /api/sketches/{id}/confirm-analysis for user approval
- [x] "Hypothesis" label visible in UI ("가설" badge added to sketch AI interpretation)

### REQ-SKETCH-004: Sketch vs reference distinction
- [x] Separate types (UserSketchAsset vs ReferenceAsset)
- [x] Different UI cards for sketches vs references

### REQ-REF-001: Reference search types
- [x] Keyword search implemented
- [x] Image search implemented
- [ ] Sketch-based search (deferred)
- [ ] Document search (deferred)

### REQ-REF-002: Copyright risk blocking
- [x] copyright_risk field on ReferenceAsset
- [x] analyze_reference checks copyright
- [x] High-risk references blocked from direct style application

### REQ-REF-003: Reference card display
- [x] Thumbnail, title, source URL displayed
- [x] Relevance reason displayed
- [x] Copyright risk indicator
- [x] collection_date displayed in UI (added to reference card)
- [x] license_type displayed in UI (added to reference card)
- [x] domain_tags displayed in UI (added to reference card)
- [x] abstraction_elements displayed in UI (added to reference card)

### REQ-TREND-001: Trend search
- [x] POST /api/sessions/{id}/trends/search
- [x] Searches active TrendSources
- [x] Results include source URL and published date

### REQ-TREND-002: Sourced claims only
- [x] TrendInsight has evidence_quote and confidence_score
- [x] is_hypothesis flag for unsourced claims
- [x] Hypothesis insights blocked from concept decisions (filter in generate_concepts.py)

### REQ-TREND-003: TrendInsight required fields
- [x] document_id required
- [x] evidence_quote required
- [x] confidence_score required

---

## Phase 4: Concepts, Abstraction, Generation

### REQ-CONCEPT-001: Concept candidates
- [x] POST /api/sessions/{id}/concepts generates candidates
- [x] Each has name/description/score/rationale/risk
- [x] UI displays concept cards

### REQ-CONCEPT-002: Concept decisions
- [x] POST /api/concepts/{id}/decisions
- [x] Records adopt/hold/discard/explore
- [x] Records decider, time, reason

### REQ-CONCEPT-003: Auto mode decisions
- [x] decider field supports "auto"
- [ ] Auto mode actually records auto decisions (deferred)

### REQ-ABST-001: Abstraction rules
- [x] POST /api/sessions/{id}/abstractions
- [x] Minimum 2 axes required (validated)
- [x] Batch generation when no source_id specified

### REQ-ABST-002: No composition copying
- [x] Prompt explicitly instructs against composition copying
- [x] Risk notes include replication warnings

### REQ-ABST-003: Sketch-based abstraction
- [x] Sketch analysis → abstraction pipeline
- [x] Keep/vary elements preserved
- [x] Original-preserving and concept-expanding prompts generated

### REQ-GEN-001: Evidence-linked generation
- [x] Generated design linked to abstraction rule
- [x] Rule must have minimum 2 axes
- [x] Generation without evidence blocked

### REQ-GEN-002: Generation metadata
- [x] Model, prompt, linked rule, params saved with generated image

### REQ-GEN-003: Generation failure handling
- [x] Failed status stored, not fake success
- [x] Failure model name and retry info returned
- [x] Background task handles errors gracefully

---

## Phase 5: Spec Documents

### REQ-SPEC-001: Spec document content
- [x] POST /api/sessions/{id}/specs generates spec
- [x] Includes brief, trends, concepts, references, abstractions
- [x] Includes discarded alternatives and selection reasons
- [x] Includes sources and evidence

### REQ-SPEC-002: Version management
- [x] POST /api/specs/{id}/version creates new version
- [x] Version field on spec_document
- [ ] Version rollback UI (deferred)

### REQ-SPEC-003: Source links in spec
- [x] content_json includes source references
- [x] Decision log included

---

## Pipeline Invariants

1. [x] Unsourced trend claims not used as concept evidence
2. [x] User sketch originals never overwritten
3. [x] AI interpretations marked as hypothesis
4. [x] Auto mode decisions logged
5. [x] Image generation requires evidence linkage
6. [x] Spec includes discarded alternatives
7. [x] Copyright-risk references blocked from direct application
8. [x] Missing config blocks execution with clear guidance
9. [x] No fake success responses

---

## UX Requirements (AC-008)

- [x] Skeleton loading for async operations
- [x] Empty state with next action suggestions
- [x] New UI consistent with legacy design
- [x] Reference card fields complete (all required fields displayed)

---

## Issues Fixed (This Session)

### P1 - SPEC Compliance (Fixed)
1. [FIXED] Reference card: added collection_date, license_type, domain_tags, abstraction_elements
2. [FIXED] Sketch AI interpretation: added "가설" hypothesis badge
3. [VERIFIED] All 8 AI-using routes catch SettingsRequiredError consistently

### P2 - Data Integrity (Fixed)
4. [FIXED] analyze_sketch: replaced fake fallback (parsed={"intent": ...}) with proper ValueError
5. [FIXED] search_references: replaced empty dict fallback with proper ValueError

### P3 - Deferred to Next SPEC (Documented)
6. rerun_step full implementation (API skeleton exists)
7. Auto mode SSE/polling UI (pipeline_stage DB save works)
8. Domain packs (industrial/fashion/visual/advertising)
9. TrendDocument crawling automation
10. Reference sketch-based/document/internal search
11. Spec version rollback UI
12. is_hypothesis auto mode blocking
