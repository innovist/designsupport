# SPEC-03-CREATION Developer Quick Reference

## Quick Start

### Architecture Overview
```
apps/
├── concepts/          # Concept candidates & decisions
│   ├── domain/        # Entities: ConceptCandidate, ConceptDecision
│   ├── application/   # Use cases: generate_concepts, propose_concept, decide_concept
│   └── infrastructure/# ORM models, repositories
├── abstraction/       # 6-axis abstraction & prompts
│   ├── domain/        # Entities: AbstractionRule, SketchPrompt, PromptPattern
│   ├── application/   # Use cases: generate_abstraction_rules, build_prompt
│   └── infrastructure/# ORM models, repositories
├── generation/        # Image generation
│   ├── domain/        # Entities: GenerationJob, GeneratedDesign, DomainPack
│   ├── application/   # Use cases: create_job, execute_generation
│   ├── infrastructure/# ORM models, image provider stubs
│   └── domain_packs/  # Domain configurations (industrial, fashion, visual, advertising)
└── specs/             # Spec document builder
    ├── domain/        # Entities: SpecDocument, DomainPack
    ├── application/   # Use cases: create_spec, approve_spec, version_spec
    └── infrastructure/# ORM models, repositories
```

## Common Use Cases

### 1. Generate Concept Candidates
```python
from apps.concepts.application.use_cases.generate_concepts import GenerateConceptsUseCase
from apps.concepts.application.dtos import GenerateConceptsRequest

# Prepare request
request = GenerateConceptsRequest(
    session_id=uuid4(),
    count=5,  # 3-5 concepts
    created_by=user_id,
)

# Execute use case
use_case = GenerateConceptsUseCase(
    concept_repository=concept_repo,
    session_port=session_port,
    trend_insight_port=trend_insight_port,
    reference_analysis_port=ref_analysis_port,
    scorer=ConceptScorer(),
    ai_generation_service=ai_service,
)

result = await use_case.execute(request)

if result.is_success():
    concepts = result.value
    for concept in concepts:
        print(f"Concept: {concept.title}, Score: {concept.score}")
else:
    print(f"Error: {result.error}")
```

### 2. Generate Abstraction Rules
```python
from apps.abstraction.application.use_cases.generate_abstraction_rules import GenerateAbstractionRulesUseCase

use_case = GenerateAbstractionRulesUseCase(
    abstraction_repository=abstraction_repo,
    concept_repository=concept_repo,
    reference_port=reference_port,
    service=AbstractionService(),
)

result = await use_case.execute(concept_id, session_id)

if result.is_success():
    rules = result.value
    for rule in rules:
        print(f"Rule: {rule.axis} - {rule.applied_rule}")
        if rule.risk_note:
            print(f"⚠️  Risk: {rule.risk_note}")
```

### 3. Create Generation Job
```python
from apps.generation.application.use_cases.create_generation_job import CreateGenerationJobUseCase
from apps.generation.application.dtos import CreateGenerationJobRequest

request = CreateGenerationJobRequest(
    session_id=session_id,
    kind=GenerationKind.SKETCH,
    brief_id=brief_id,
    concept_id=concept_id,
    reference_ids=reference_ids,
    model_policy_key="default",
)

use_case = CreateGenerationJobUseCase(
    job_repository=job_repo,
    design_repository=design_repo,
    session_port=session_port,
    model_router_port=model_router_port,
)

result = await use_case.execute(request)

if result.is_success():
    job = result.value
    print(f"Job created: {job.id}, Status: {job.status}")
```

### 4. Build Spec Document
```python
from apps.specs.application.use_cases.create_spec_document import CreateSpecDocumentUseCase
from apps.specs.application.dtos import CreateSpecRequest

request = CreateSpecRequest(
    session_id=session_id,
    created_by=user_id,
)

use_case = CreateSpecDocumentUseCase(
    spec_repository=spec_repo,
    session_port=session_port,
    concept_port=concept_port,
    abstraction_port=abstraction_port,
    generation_port=generation_port,
    domain_pack_loader=domain_pack_loader,
)

result = await use_case.execute(request)

if result.is_success():
    spec = result.value
    print(f"Spec created: {spec.id}, Domain: {spec.domain}")
    print(f"Sections: {len(spec.sections)}")
```

### 5. Version Spec Document
```python
from apps.specs.application.use_cases.version_spec import VersionSpecUseCase
from apps.specs.application.dtos import VersionSpecRequest

request = VersionSpecRequest(
    spec_id=spec_id,
    created_by=user_id,
    version_diff=VersionDiffDTO(
        previous_version_id=str(old_spec.id),
        new_version_id="",  # Will be generated
        changes=["Updated concept section", "Added new images"],
        changed_sections=["concept_candidates", "generated_images"],
        change_summary="Updated based on new feedback",
    ),
)

use_case = VersionSpecUseCase(spec_repository=spec_repo)
result = await use_case.execute(request)

if result.is_success():
    new_spec = result.value
    print(f"New version: {new_spec.version}, Supersedes: {new_spec.supersedes_id}")
```

## Key Patterns

### Error Handling with Result Pattern
```python
from shared.application.result import Result

# Always check result
result = await use_case.execute(request)
if result.is_success():
    data = result.value
    # Process data
else:
    error = result.error
    # Handle error
```

### Entity Validation
```python
from shared.domain.exceptions import ValidationError

try:
    concept = ConceptCandidate(
        session_id=session_id,
        title=title,
        description=description,
        rationale=rationale,
        rationale_refs=rationale_refs,  # Must have ≥1
        created_by=user_id,
    )
except ValidationError as e:
    print(f"Validation error: {e.field} - {e.message}")
```

### Repository Pattern
```python
# Find by ID
result = await repository.find_by_id(entity_id)
if result.is_success():
    entity = result.value

# Save entity
saved_entity = await repository.save(entity)

# Find by session
entities = await repository.find_by_session(session_id, limit=50)
```

## Domain Packs

### Available Domains
- **industrial**: Product design, manufacturing, ergonomics
- **fashion**: Garment design, fabrics, styling
- **visual**: Graphic design, branding, visual systems
- **advertising**: Campaign concepts, copy, media

### Using Domain Packs
```python
from apps.specs.application.use_cases.list_domain_packs import ListDomainPacksUseCase

use_case = ListDomainPacksUseCase(domain_pack_loader=loader)
result = await use_case.execute()

if result.is_success():
    packs = result.value
    for pack in packs:
        print(f"{pack.domain}: {pack.evaluation_axes}")
        print(f"Outputs: {pack.generation_outputs}")
```

## Traceability

### All Outputs Link Back
- **GenerationJob** → brief_id, concept_id, rule_ids, reference_ids
- **GeneratedDesign** → job_id, brief_id, concept_id, rule_ids, reference_ids
- **SpecDocument** → Must reference all before approval

### Evidence Links
```python
# Add evidence to spec section
spec.update_section(
    section_type="concept_candidates",
    content={"concepts": [...]},
    evidence_links=[str(concept_id) for concept_id in concept_ids],
)

# Add global evidence link
spec.add_evidence_link(str(abstraction_rule_id))
```

## Safety Features

### Prompt Safety Validation
```python
from apps.abstraction.application.use_cases.validate_prompt_safety import ValidatePromptSafetyUseCase

use_case = ValidatePromptSafetyUseCase(
    violation_repository=violation_repo,
    prompt_policy_port=policy_port,
)

result = await use_case.execute(prompt_text, session_id)

if result.is_success():
    validation = result.value
    if not validation.is_safe:
        print(f"⚠️  Violations: {validation.violations}")
```

### Style Mimicry Rejection
```python
# AbstractionService automatically rejects:
# - Direct brand name mentions
# - Specific artist names
# - High-risk license references

# Check risk notes
if rule.risk_note:
    print(f"Rule flagged: {rule.risk_note}")
```

## Testing

### Unit Test Example
```python
import pytest
from apps.concepts.domain.entities import ConceptCandidate, ConceptStatus
from shared.domain.exceptions import ValidationError

def test_concept_requires_rationale_refs():
    with pytest.raises(ValidationError) as exc:
        ConceptCandidate(
            session_id=uuid4(),
            title="Test",
            description="Test",
            rationale="Test",
            rationale_refs=[],  # Empty list
            created_by=uuid4(),
        )
    assert "rationale_refs" in str(exc.value)
```

### Integration Test Example
```python
@pytest.mark.asyncio
async def test_generate_concepts_use_case(
    concept_repository,
    session_port,
    trend_insight_port,
):
    use_case = GenerateConceptsUseCase(
        concept_repository=concept_repository,
        session_port=session_port,
        trend_insight_port=trend_insight_port,
        reference_analysis_port=mock(),
        scorer=ConceptScorer(),
        ai_generation_service=mock_ai_service(),
    )

    request = GenerateConceptsRequest(
        session_id=uuid4(),
        count=3,
        created_by=uuid4(),
    )

    result = await use_case.execute(request)

    assert result.is_success()
    assert len(result.value) == 3
    assert all(c.score is not None for c in result.value)
```

## Common Pitfalls

### ❌ Don't
```python
# Don't use Django imports in domain layer
from django.db import models  # ❌ Wrong place

# Don't return fake data on failure
if model_fails:
    return fake_data  # ❌ Violates REQ-03-CONCEPT-005

# Don't hardcode values
concept.score = 0.75  # ❌ Not calculated
```

### ✅ Do
```python
# Use pure Python in domain layer
from dataclasses import dataclass  # ✅ Correct

# Raise ValidationError on failure
if model_fails:
    raise ValidationError("score", "Calculation failed")  # ✅

# Calculate scores properly
concept.update_score(scorer.score_concept(...))  # ✅
```

## File Locations

### Domain Entities
- `apps/{module}/domain/entities.py`
- Pure Python, no Django imports

### Use Cases
- `apps/{module}/application/use_cases/{use_case}.py`
- Business logic orchestration

### ORM Models
- `apps/{module}/infrastructure/orm/models.py`
- Django models with to_domain/from_domain

### Repositories
- `apps/{module}/infrastructure/repositories/{repository}.py`
- Data access implementation

## Help & Resources

### Documentation
- `.moai/specs/SPEC-03-CREATION/IMPLEMENTATION_SUMMARY.md` - Full implementation details
- `.moai/specs/SPEC-03-CREATION/VALIDATION_CHECKLIST.md` - Requirements checklist
- `.moai/specs/SPEC-03-CREATION/implementation_plan.md` - Implementation plan

### Code Examples
- `apps/concepts/application/use_cases/` - Concept use cases
- `apps/abstraction/application/use_cases/` - Abstraction use cases
- `apps/generation/application/use_cases/` - Generation use cases
- `apps/specs/application/use_cases/` - Spec use cases

### Testing
- `apps/{module}/tests/` - Module-specific tests
- Target: 85%+ coverage

---

**Last Updated**: 2026-05-08
**Status**: ✅ Implementation Complete
