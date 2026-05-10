"""Tests for generation prompt construction rules."""

import pytest

from app.application.use_cases.generation.build_generation_prompt import (
    _compose_prompt,
    _validate_generated_prompt,
    image_feature_for_output,
    PROMPT_FEATURE_BY_OUTPUT,
)
from app.application.services.pipeline_orchestrator import DesignPipelineOrchestrator


def test_compose_prompt_includes_benchmarked_structure_without_examples():
    prompt = _compose_prompt(
        "Output type: final presentation image.",
        "Form: compact vertical object\nStructure: modular hinge",
        None,
    )

    assert "Use this benchmarked prompt structure" in prompt
    assert "Output artifact" in prompt
    assert "Composition" in prompt
    assert "Abstraction rule:" in prompt
    assert "compact vertical object" in prompt


def test_validate_generated_prompt_rejects_direct_imitation():
    with pytest.raises(ValueError):
        _validate_generated_prompt("A product image in the style of a named artist.")


def test_validate_generated_prompt_allows_negative_brand_constraint():
    _validate_generated_prompt("A clean product render with no copied brand marks or logos.")


def test_current_output_kinds_use_existing_workspace_feature_keys():
    assert PROMPT_FEATURE_BY_OUTPUT["draft"] == "sketch_prompt_generation"
    assert PROMPT_FEATURE_BY_OUTPUT["final"] == "final_image_prompt_generation"
    assert image_feature_for_output("draft") == "sketch_generation"
    assert image_feature_for_output("final") == "final_image_generation"


def test_auto_pipeline_generation_creates_drafts_only_even_if_final_requested():
    orchestrator = DesignPipelineOrchestrator(
        session_id="00000000-0000-0000-0000-000000000000",
        db=None,
        options={"generate_drafts": True, "generate_final_images": True},
    )

    assert orchestrator._generation_output_kinds() == ["draft"]
