# SPEC-03-CREATION Implementation Plan

## Status Assessment

### Already Implemented ✓
- apps/concepts/domain/entities.py - ConceptCandidate, ConceptDecision
- apps/concepts/domain/services.py - ConceptValidator, ConceptScorer
- apps/concepts/application/use_cases/propose_concept.py - Single concept creation
- apps/concepts/application/use_cases/decide_concept.py - Decision recording
- apps/concepts/application/use_cases/list_concepts.py - List concepts
- apps/abstraction/domain/entities.py - AbstractionRule, SketchPrompt, PromptPattern, PromptSafetyViolation
- apps/abstraction/domain/services.py - AbstractionService, PromptBuilder
- apps/abstraction/application/use_cases/generate_abstraction_rules.py
- apps/abstraction/application/use_cases/generate_sketch_prompts.py
- apps/abstraction/application/use_cases/validate_prompt_safety.py
- apps/generation/domain/entities.py - GenerationJob, GeneratedDesign
- apps/generation/application/use_cases/create_generation_job.py
- apps/generation/application/use_cases/execute_generation_job.py
- apps/generation/application/use_cases/get_generation_result.py
- apps/specs/domain/entities.py - SpecDocument, DomainPack
- apps/specs/application/use_cases/create_spec_document.py
- apps/specs/application/use_cases/approve_spec.py
- apps/specs/application/use_cases/reject_spec.py
- apps/specs/application/use_cases/submit_for_review.py
- apps/specs/application/use_cases/get_spec_document.py
- apps/specs/application/use_cases/list_domain_packs.py

### Missing Implementation ✗

1. **apps/concepts/application/use_cases/generate_concepts.py**
   - Bulk generation of 3-5 concept candidates using AI
   - Should call ConceptScoringService for each candidate
   - REQ-03-CONCEPT-005: Never return fake scores on model failure

2. **apps/generation/domain/entities.py - DomainPack enhancement**
   - Add generation_outputs field
   - Validate domain pack structure

3. **apps/generation/infrastructure/image_providers/** - Provider stubs
   - seedream_adapter.py (ByteDance Seedream 4.5 via BytePlus Ark)
   - alibaba_zimage_adapter.py (Alibaba z-image-turbo)
   - gemini_image_adapter.py (Google Gemini)
   - openai_image_adapter.py (OpenAI gpt-image-2)
   - Note: These are stubs - SPEC-04 ModelRouter owns actual implementation

4. **apps/generation/domain_packs/** - Seed data
   - domain_packs/industrial/manifest.yaml
   - domain_packs/fashion/manifest.yaml
   - domain_packs/visual/manifest.yaml
   - domain_packs/advertising/manifest.yaml

5. **apps/specs/application/use_cases/version_spec.py**
   - Create new version of spec document
   - Handle superseding logic

## Implementation Priority

1. **High Priority**
   - generate_concepts.py - Core AI feature
   - DomainPack enhancement - Required for generation
   - version_spec.py - Required for spec workflow

2. **Medium Priority**
   - Image provider stubs - Integration points for SPEC-04
   - Domain pack seed data - Configuration

## Implementation Approach

Follow existing patterns:
- Use 4-layer clean architecture (domain → application → infrastructure → presentation)
- Domain entities are pure Python (no Django imports)
- Use ports for infrastructure dependencies
- Use Result pattern for error handling
- Use DTOs for data transfer
- All traceability requirements enforced

## File Size Limits

- Maximum 1000 LOC per file
- Maximum 100 LOC per function
- Split large files into smaller modules
