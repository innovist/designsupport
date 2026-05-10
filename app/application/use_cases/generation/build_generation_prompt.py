"""
Build image-model prompts for generation outputs.
"""

from __future__ import annotations

import uuid
import re

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIMessage
from app.infrastructure.ai_clients.factory import get_ai_client
from app.models.abstraction import AbstractionRule
from app.models.concepts import ConceptCandidate

DRAFT_OUTPUT = "draft"
FINAL_OUTPUT = "final"
OUTPUT_KINDS = (DRAFT_OUTPUT, FINAL_OUTPUT)

# Legacy value map: old DB records use "sketch"/"final_image"; normalize at read time.
LEGACY_KIND_MAP: dict[str, str] = {
    "sketch": DRAFT_OUTPUT,
    "final_image": FINAL_OUTPUT,
}

PROMPT_FEATURE_BY_OUTPUT = {
    DRAFT_OUTPUT: "sketch_prompt_generation",
    FINAL_OUTPUT: "final_image_prompt_generation",
}

IMAGE_FEATURE_BY_OUTPUT = {
    DRAFT_OUTPUT: "sketch_generation",
    FINAL_OUTPUT: "final_image_generation",
}


def normalize_output_kind(kind: str) -> str:
    """Map legacy output_kind values to current canonical values."""
    return LEGACY_KIND_MAP.get(kind, kind)

_PROMPT_RULES = """
Write one production-ready prompt for an image generation model.
Use only the supplied visual concept and abstraction rule. Do not invent evidence.
Do not name living artists, brands, copyrighted characters, or source works.
Do not request direct copying of a reference image.
Keep the prompt concrete, visual, and concise.
Return plain text only.
"""

_BENCHMARK_METHOD = """
Use this benchmarked prompt structure without copying any external prompt:
1. Output artifact: identify whether this is a sketch, product view, scene, board, material study, or presentation image.
2. Subject anchor: describe the object, garment, interface, space, or visual system being generated.
3. Design grammar: translate form, structure, surface, color/material, meaning, and usability into visible features.
4. Composition: specify viewpoint, framing, scale, layout density, and whether labels or text should appear.
5. Rendering behavior: state finish level, line quality or material realism, lighting, background, and context.
6. Preservation/change rules: say what must remain consistent and what may vary.
7. Quality constraints: require coherent proportions, readable structure, no copied brand marks, no artist imitation.
"""

_DRAFT_DIRECTION = """
Output type: draft design concept image.
Prioritize clear silhouette, primary form, structural intent, and design direction.
This is a directional draft — show the design idea clearly without overworking details.
"""

_FINAL_IMAGE_DIRECTION = """
Output type: final presentation image.
Prioritize finished material appearance, lighting, color, surface detail, use context, and polished product/fashion presentation.
Avoid unfinished sketch language.
"""

_DIRECT_IMITATION_PATTERNS = (
    re.compile(r"\bin\s+the\s+style\s+of\b", re.IGNORECASE),
    re.compile(r"\bas\s+if\s+.*\bmade\s+by\b", re.IGNORECASE),
    re.compile(r"\bcopy\s+the\b", re.IGNORECASE),
    re.compile(r"\bdirect\s+replica\b", re.IGNORECASE),
    re.compile(r"\bexact\s+replica\b", re.IGNORECASE),
    re.compile(r"\b(include|add|with|visible)\s+.*\bbrand\s+logo\b", re.IGNORECASE),
)


# @MX:ANCHOR: [AUTO] build_generation_prompt — core prompt builder called by create_generation_job and pipeline_orchestrator
# @MX:REASON: [AUTO] fan_in >= 2 callers; signature change (feedback_note) propagates to all callers
async def build_generation_prompt(
    db: Session,
    rule: AbstractionRule | None,
    output_kind: str,
    concept_id: uuid.UUID | None = None,
    feedback_note: str | None = None,
) -> str:
    """Generate the prompt text for a draft or final output.

    output_kind accepts current values ("draft", "final") and legacy values
    ("sketch", "final_image") which are normalized transparently.
    """
    normalized_kind = normalize_output_kind(output_kind)
    if normalized_kind not in OUTPUT_KINDS:
        raise ValueError(f"Unsupported generation output kind: {output_kind!r}")

    rule_text = _serialize_rule(rule) if rule else None
    concept_text = _serialize_concept(db.get(ConceptCandidate, concept_id)) if concept_id else None
    if not rule_text and not concept_text:
        raise ValueError("이미지 프롬프트 작성에는 컨셉 또는 추상화 규칙이 필요합니다.")
    client = await get_ai_client(db, PROMPT_FEATURE_BY_OUTPUT[normalized_kind])
    direction = _DRAFT_DIRECTION if normalized_kind == DRAFT_OUTPUT else _FINAL_IMAGE_DIRECTION
    response = await client.complete(
        [
            AIMessage(
                role="user",
                content=_compose_prompt(
                    direction,
                    rule_text,
                    concept_text,
                    feedback_note if normalized_kind == FINAL_OUTPUT else None,
                ),
            )
        ],
        temperature=0.35,
        max_tokens=700,
    )
    prompt = response.content.strip()
    _validate_generated_prompt(prompt)
    return prompt


def image_feature_for_output(output_kind: str) -> str:
    normalized_kind = normalize_output_kind(output_kind)
    if normalized_kind not in IMAGE_FEATURE_BY_OUTPUT:
        raise ValueError(f"Unsupported generation output kind: {output_kind!r}")
    return IMAGE_FEATURE_BY_OUTPUT[normalized_kind]


def _compose_prompt(
    direction: str,
    rule_text: str,
    concept_text: str | None,
    feedback_note: str | None = None,
) -> str:
    feedback_line = f"User feedback to incorporate: {feedback_note}" if feedback_note else ""
    return "\n".join(
        part
        for part in (
            _PROMPT_RULES.strip(),
            _BENCHMARK_METHOD.strip(),
            direction.strip(),
            "Selected visual concept:",
            concept_text,
            feedback_line,
            "Abstraction rule:",
            rule_text,
        )
        if part
    )


def _validate_generated_prompt(prompt: str) -> None:
    if not prompt:
        raise ValueError("이미지 프롬프트 작성 모델이 빈 응답을 반환했습니다.")
    for pattern in _DIRECT_IMITATION_PATTERNS:
        if pattern.search(prompt):
            raise ValueError("이미지 프롬프트에 직접 모사 또는 브랜드 고정 표현이 포함되었습니다.")


def _serialize_rule(rule: AbstractionRule) -> str:
    labels = {
        "form": "Form",
        "structure": "Structure",
        "surface": "Surface",
        "color_material": "Color and material",
        "meaning": "Meaning",
        "usability": "Usability",
        "risk_notes": "Risks to avoid",
    }
    lines = [
        f"{label}: {value}"
        for field, label in labels.items()
        if (value := getattr(rule, field, None))
    ]
    return "\n".join(lines)


def _serialize_concept(concept: ConceptCandidate | None) -> str | None:
    if not concept:
        return None
    lines = [
        f"Name: {concept.name}" if concept.name else None,
        f"Visual direction: {concept.description}" if concept.description else None,
        f"Design rationale: {concept.rationale}" if concept.rationale else None,
        f"Design risk: {concept.risk}" if concept.risk else None,
    ]
    return "\n".join(line for line in lines if line)
