"""Unit tests for abstraction domain services.

Tests cover rule validation, risk detection, and prompt building.
"""
import pytest
from uuid import uuid4

from apps.abstraction.domain.services import (
    AbstractionRuleValidator,
    SketchPromptBuilder,
)
from apps.abstraction.domain.entities import AbstractionRule
from apps.abstraction.domain.value_objects import (
    AbstractionAxis,
    RiskLevel,
)
from shared.domain.exceptions import ValidationError


class TestAbstractionRuleValidator:
    """Test abstraction rule validation for brand mimicry and license risks."""

    def test_valid_rule_passes_validation(self):
        """Test that a valid rule passes validation."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.FORM,
            observation="The concept uses geometric shapes",
            applied_rule="Use geometric primitives to define form structure",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(rule)

        assert is_valid is True
        assert reason is None

    def test_rule_with_unknown_license_risk_passes_if_safe(self):
        """Test that rule with UNKNOWN license risk passes if content is safe."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.SURFACE,
            observation="Matte finish with subtle texture",
            applied_rule="Apply matte finish with tactile texture",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(
            rule,
            license_risk=RiskLevel.UNKNOWN
        )

        assert is_valid is True
        assert reason is None

    def test_brand_mimicry_in_style_of_pattern(self):
        """Test detection of 'in the style of' brand mimicry pattern."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.MEANING,
            observation="Design in the style of Apple minimalist aesthetic",
            applied_rule="Copy Apple's minimalist design language",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(rule)

        assert is_valid is False
        assert reason is not None
        assert "mimics" in reason.lower() or "apple" in reason.lower()
        assert rule.risk_note == reason

    def test_brand_mimicry_mimicking_pattern(self):
        """Test detection of 'mimicking' brand mimicry pattern."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.FORM,
            observation="Design mimicking Apple bold typography",
            applied_rule="Use Apple style bold typography",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(rule)

        assert is_valid is False
        assert reason is not None
        assert "apple" in reason.lower()

    def test_known_artist_detection(self):
        """Test detection of known artist name in rule."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.COLOR_MATERIAL,
            observation="Use color palette in the style of Picasso",
            applied_rule="Apply Picasso inspired color scheme",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(rule)

        assert is_valid is False
        assert reason is not None
        assert "picasso" in reason.lower()

    def test_high_license_risk_with_exact_copy(self):
        """Test detection of high license risk with 'exact copy' pattern."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.FORM,
            observation="Exact copy of original design",
            applied_rule="Replicate the design exactly as shown",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(
            rule,
            license_risk=RiskLevel.HIGH
        )

        assert is_valid is False
        assert reason is not None
        assert "copy" in reason.lower() or "replicate" in reason.lower()

    def test_high_license_risk_with_replicate(self):
        """Test detection of 'replicate' pattern with high license risk."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.STRUCTURE,
            observation="Structure to replicate from reference",
            applied_rule="Replicate the structural elements",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(
            rule,
            license_risk=RiskLevel.HIGH
        )

        assert is_valid is False
        assert reason is not None

    def test_medium_license_risk_with_safe_content_passes(self):
        """Test that MEDIUM license risk passes with safe content."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.USABILITY,
            observation="Simple button layout for ease of use",
            applied_rule="Use simple, intuitive button layout",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(
            rule,
            license_risk=RiskLevel.MEDIUM
        )

        assert is_valid is True
        assert reason is None

    def test_low_license_risk_always_passes(self):
        """Test that LOW license risk always passes validation."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.FORM,
            observation="Geometric form with clean lines",
            applied_rule="Use geometric shapes with clean edges",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(
            rule,
            license_risk=RiskLevel.LOW
        )

        assert is_valid is True
        assert reason is None

    def test_trace_pattern_detected_as_high_risk(self):
        """Test that 'trace' pattern is detected as high license risk."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.FORM,
            observation="Trace the outline from reference image",
            applied_rule="Trace the form directly",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(
            rule,
            license_risk=RiskLevel.HIGH
        )

        assert is_valid is False
        assert reason is not None

    def test_case_insensitive_brand_detection(self):
        """Test that brand detection is case-insensitive."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.MEANING,
            observation="Design inspired by SAMSUNG exactly",
            applied_rule="Follow Samsung's design language",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(rule)

        assert is_valid is False
        assert reason is not None

    def test_rule_without_brand_name_passes(self):
        """Test that rule without brand/artist name passes."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.SURFACE,
            observation="Clean surface with subtle texture",
            applied_rule="Apply matte finish with minimal texture",
        )

        is_valid, reason = AbstractionRuleValidator.validate_rule(rule)

        assert is_valid is True
        assert reason is None


class TestSketchPromptBuilder:
    """Test sketch prompt building from abstraction rules."""

    def test_build_preserve_original_prompt_success(self):
        """Test successful preserve_original prompt building."""
        session_id = uuid4()

        rules = [
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.FORM,
                observation="Geometric shapes",
                applied_rule="Use geometric primitives",
            ),
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.SURFACE,
                observation="Matte finish",
                applied_rule="Apply matte texture",
            ),
        ]

        sketch_analysis = {
            "keep_elements": ["geometric form", "minimalist style"],
            "modifiable_elements": ["color palette", "material finish"],
        }

        template, variables, source_refs = SketchPromptBuilder.build_preserve_original_prompt(
            session_id=session_id,
            abstraction_rules=rules,
            sketch_analysis=sketch_analysis,
        )

        assert "PRESERVES" in template
        assert "EXPLORES" in template
        assert variables["keep_elements"] == "- geometric form\n- minimalist style"
        assert variables["modifiable_elements"] == "- color palette\n- material finish"
        assert "[form]" in variables["design_principles"]
        assert "[surface]" in variables["design_principles"]
        assert len(source_refs) == 2

    def test_build_preserve_original_empty_rules_raises_error(self):
        """Test that empty rules list raises ValidationError."""
        sketch_analysis = {
            "keep_elements": ["form"],
            "modifiable_elements": ["color"],
        }

        with pytest.raises(ValidationError) as exc_info:
            SketchPromptBuilder.build_preserve_original_prompt(
                session_id=uuid4(),
                abstraction_rules=[],
                sketch_analysis=sketch_analysis,
            )

        assert exc_info.value.field == "abstraction_rules"
        assert "at least one" in str(exc_info.value).lower()

    def test_build_expand_concept_prompt_success(self):
        """Test successful expand_concept prompt building."""
        session_id = uuid4()

        rules = [
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.FORM,
                observation="Organic curves",
                applied_rule="Explore organic, flowing forms",
            ),
        ]

        sketch_analysis = {
            "core_identity": "sustainable packaging design",
        }

        template, variables, source_refs = SketchPromptBuilder.build_expand_concept_prompt(
            session_id=session_id,
            abstraction_rules=rules,
            sketch_analysis=sketch_analysis,
        )

        assert "EXPANDS" in template
        assert "Core concept identity" in template
        assert variables["core_identity"] == "sustainable packaging design"
        assert "[form]" in variables["design_principles"]
        assert "Explore form:" in variables["exploration_directions"]
        assert len(source_refs) == 1

    def test_build_expand_concept_empty_rules_raises_error(self):
        """Test that empty rules list raises ValidationError."""
        sketch_analysis = {
            "core_identity": "test identity",
        }

        with pytest.raises(ValidationError) as exc_info:
            SketchPromptBuilder.build_expand_concept_prompt(
                session_id=uuid4(),
                abstraction_rules=[],
                sketch_analysis=sketch_analysis,
            )

        assert exc_info.value.field == "abstraction_rules"

    def test_build_preserve_original_with_empty_elements(self):
        """Test prompt building with empty element lists."""
        session_id = uuid4()

        rules = [
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.FORM,
                observation="Test",
                applied_rule="Test rule",
            ),
        ]

        sketch_analysis = {
            "keep_elements": [],
            "modifiable_elements": [],
        }

        template, variables, source_refs = SketchPromptBuilder.build_preserve_original_prompt(
            session_id=session_id,
            abstraction_rules=rules,
            sketch_analysis=sketch_analysis,
        )

        assert variables["keep_elements"] == "none"
        assert variables["modifiable_elements"] == "none"

    def test_build_expand_concept_with_missing_core_identity(self):
        """Test expand_concept with missing core_identity uses default."""
        session_id = uuid4()

        rules = [
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.FORM,
                observation="Test",
                applied_rule="Test rule",
            ),
        ]

        sketch_analysis = {}  # No core_identity

        template, variables, source_refs = SketchPromptBuilder.build_expand_concept_prompt(
            session_id=session_id,
            abstraction_rules=rules,
            sketch_analysis=sketch_analysis,
        )

        assert variables["core_identity"] == "the original concept"

    def test_format_rules_with_multiple_axes(self):
        """Test that rules are formatted correctly with multiple axes."""
        session_id = uuid4()

        rules = [
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.FORM,
                observation="Geometric",
                applied_rule="Form rule",
            ),
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.SURFACE,
                observation="Matte",
                applied_rule="Surface rule",
            ),
            AbstractionRule(
                session_id=session_id,
                concept_id=uuid4(),
                axis=AbstractionAxis.MEANING,
                observation="Minimalist",
                applied_rule="Meaning rule",
            ),
        ]

        formatted = SketchPromptBuilder._format_rules(rules)

        assert "[form] Form rule" in formatted
        assert "[surface] Surface rule" in formatted
        assert "[meaning] Meaning rule" in formatted

    def test_build_exploration_directions_with_all_axes(self):
        """Test exploration directions building with all six axes."""
        session_id = uuid4()

        rules = []
        for axis in AbstractionAxis.all_axes():
            rules.append(
                AbstractionRule(
                    session_id=session_id,
                    concept_id=uuid4(),
                    axis=axis,
                    observation=f"{axis.value} observation",
                    applied_rule=f"{axis.value} rule",
                )
            )

        directions = SketchPromptBuilder._build_exploration_directions(rules)

        # Check all axes are represented
        assert "Explore form:" in directions
        assert "Explore structure:" in directions
        assert "Explore surface:" in directions
        assert "Explore color_material:" in directions
        assert "Explore meaning:" in directions
        assert "Explore usability:" in directions

    def test_build_exploration_directions_empty_rules(self):
        """Test exploration directions with no rules returns default."""
        directions = SketchPromptBuilder._build_exploration_directions([])

        assert directions == "Explore all design dimensions"
