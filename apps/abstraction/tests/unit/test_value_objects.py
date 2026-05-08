"""Unit tests for abstraction value objects.

Tests cover enum values and validation.
"""
import pytest
from uuid import uuid4

from apps.abstraction.domain.value_objects import (
    AbstractionAxis,
    SketchPromptKind,
    PromptCategory,
    RiskLevel,
)


class TestAbstractionAxis:
    """Test AbstractionAxis enum."""

    def test_six_axes_exist(self):
        """Test that all six abstraction axes are defined."""
        axes = list(AbstractionAxis)

        assert len(axes) == 6

        axis_values = [axis.value for axis in axes]
        assert "form" in axis_values
        assert "structure" in axis_values
        assert "surface" in axis_values
        assert "color_material" in axis_values
        assert "meaning" in axis_values
        assert "usability" in axis_values

    def test_all_axes_classmethod(self):
        """Test that all_axes() returns all six axes."""
        all_axes = AbstractionAxis.all_axes()

        assert len(all_axes) == 6
        assert isinstance(all_axes, list)
        assert all(isinstance(axis, AbstractionAxis) for axis in all_axes)

    def test_axis_values_are_strings(self):
        """Test that all axis values are strings."""
        for axis in AbstractionAxis:
            assert isinstance(axis.value, str)
            assert len(axis.value) > 0

    def test_form_axis(self):
        """Test FORM axis."""
        assert AbstractionAxis.FORM.value == "form"
        assert AbstractionAxis.FORM == AbstractionAxis.FORM

    def test_structure_axis(self):
        """Test STRUCTURE axis."""
        assert AbstractionAxis.STRUCTURE.value == "structure"

    def test_surface_axis(self):
        """Test SURFACE axis."""
        assert AbstractionAxis.SURFACE.value == "surface"

    def test_color_material_axis(self):
        """Test COLOR_MATERIAL axis."""
        assert AbstractionAxis.COLOR_MATERIAL.value == "color_material"

    def test_meaning_axis(self):
        """Test MEANING axis."""
        assert AbstractionAxis.MEANING.value == "meaning"

    def test_usability_axis(self):
        """Test USABILITY axis."""
        assert AbstractionAxis.USABILITY.value == "usability"


class TestSketchPromptKind:
    """Test SketchPromptKind enum."""

    def test_two_kinds_exist(self):
        """Test that exactly two prompt kinds are defined."""
        kinds = list(SketchPromptKind)

        assert len(kinds) == 2

    def test_preserve_original_kind(self):
        """Test PRESERVE_ORIGINAL kind."""
        assert SketchPromptKind.PRESERVE_ORIGINAL.value == "preserve_original"
        assert "preserve" in SketchPromptKind.PRESERVE_ORIGINAL.value

    def test_expand_concept_kind(self):
        """Test EXPAND_CONCEPT kind."""
        assert SketchPromptKind.EXPAND_CONCEPT.value == "expand_concept"
        assert "expand" in SketchPromptKind.EXPAND_CONCEPT.value

    def test_kind_values_are_strings(self):
        """Test that all kind values are strings."""
        for kind in SketchPromptKind:
            assert isinstance(kind.value, str)

    def test_enum_comparison(self):
        """Test enum comparison works correctly."""
        assert SketchPromptKind.PRESERVE_ORIGINAL == SketchPromptKind.PRESERVE_ORIGINAL
        assert SketchPromptKind.PRESERVE_ORIGINAL != SketchPromptKind.EXPAND_CONCEPT


class TestPromptCategory:
    """Test PromptCategory enum."""

    def test_ten_categories_exist(self):
        """Test that all ten prompt categories are defined."""
        categories = list(PromptCategory)

        assert len(categories) == 10

    def test_all_category_values(self):
        """Test that all expected category values are present."""
        category_values = [cat.value for cat in PromptCategory]

        expected_categories = [
            "line_to_render",
            "multi_reference_fusion",
            "product_packaging",
            "material_texture",
            "exploded_view",
            "storyboard",
            "moodboard_collage",
            "diagram_annotation",
            "domain_application",
            "refinement_preserve_original",
        ]

        for expected in expected_categories:
            assert expected in category_values

    def test_line_to_render_category(self):
        """Test LINE_TO_RENDER category."""
        assert PromptCategory.LINE_TO_RENDER.value == "line_to_render"

    def test_multi_reference_fusion_category(self):
        """Test MULTI_REFERENCE_FUSION category."""
        assert PromptCategory.MULTI_REFERENCE_FUSION.value == "multi_reference_fusion"

    def test_product_packaging_category(self):
        """Test PRODUCT_PACKAGING category."""
        assert PromptCategory.PRODUCT_PACKAGING.value == "product_packaging"

    def test_material_texture_category(self):
        """Test MATERIAL_TEXTURE category."""
        assert PromptCategory.MATERIAL_TEXTURE.value == "material_texture"

    def test_exploded_view_category(self):
        """Test EXPLODED_VIEW category."""
        assert PromptCategory.EXPLODED_VIEW.value == "exploded_view"

    def test_storyboard_category(self):
        """Test STORYBOARD category."""
        assert PromptCategory.STORYBOARD.value == "storyboard"

    def test_moodboard_collage_category(self):
        """Test MOODBOARD_COLLAGE category."""
        assert PromptCategory.MOODBOARD_COLLAGE.value == "moodboard_collage"

    def test_diagram_annotation_category(self):
        """Test DIAGRAM_ANNOTATION category."""
        assert PromptCategory.DIAGRAM_ANNOTATION.value == "diagram_annotation"

    def test_domain_application_category(self):
        """Test DOMAIN_APPLICATION category."""
        assert PromptCategory.DOMAIN_APPLICATION.value == "domain_application"

    def test_refinement_preserve_original_category(self):
        """Test REFINEMENT_PRESERVE_ORIGINAL category."""
        assert PromptCategory.REFINEMENT_PRESERVE_ORIGINAL.value == "refinement_preserve_original"


class TestRiskLevel:
    """Test RiskLevel enum."""

    def test_four_levels_exist(self):
        """Test that all four risk levels are defined."""
        levels = list(RiskLevel)

        assert len(levels) == 4

    def test_all_level_values(self):
        """Test that all expected risk level values are present."""
        level_values = [level.value for level in RiskLevel]

        expected_levels = ["low", "medium", "high", "unknown"]

        for expected in expected_levels:
            assert expected in level_values

    def test_low_level(self):
        """Test LOW risk level."""
        assert RiskLevel.LOW.value == "low"

    def test_medium_level(self):
        """Test MEDIUM risk level."""
        assert RiskLevel.MEDIUM.value == "medium"

    def test_high_level(self):
        """Test HIGH risk level."""
        assert RiskLevel.HIGH.value == "high"

    def test_unknown_level(self):
        """Test UNKNOWN risk level."""
        assert RiskLevel.UNKNOWN.value == "unknown"

    def test_level_ordering(self):
        """Test that risk levels can be compared by value if needed."""
        # Note: Enums don't have natural ordering, but we can check string values
        levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.UNKNOWN]

        for level in levels:
            assert isinstance(level.value, str)
            assert len(level.value) > 0

    def test_all_levels_are_unique(self):
        """Test that all risk levels have unique values."""
        level_values = [level.value for level in RiskLevel]

        assert len(level_values) == len(set(level_values)), "All risk level values must be unique"


class TestValueObjectIntegration:
    """Integration tests for value objects."""

    def test_abstraction_axis_in_entities(self):
        """Test that AbstractionAxis can be used in entity validation."""
        from apps.abstraction.domain.entities import AbstractionRule

        valid_axes = list(AbstractionAxis)

        for axis in valid_axes:
            # Should not raise any errors
            rule = AbstractionRule(
                session_id=uuid4(),
                concept_id=uuid4(),
                axis=axis,
                observation="Test observation",
                applied_rule="Test rule",
            )
            assert rule.axis == axis

    def test_sketch_prompt_kind_in_prompts(self):
        """Test that SketchPromptKind can be used in prompt creation."""
        from apps.abstraction.domain.entities import SketchPrompt

        for kind in list(SketchPromptKind):
            # Should not raise any errors
            prompt = SketchPrompt(
                session_id=uuid4(),
                kind=kind,
                template="Test template with {variable}",
                variables={"variable": "value"},
            )
            assert prompt.kind == kind

    def test_prompt_category_in_patterns(self):
        """Test that PromptCategory can be used in pattern creation."""
        from apps.abstraction.domain.entities import PromptPattern

        for category in list(PromptCategory):
            # Should not raise any errors
            pattern = PromptPattern(
                name=f"Test pattern for {category.value}",
                category=category,
                source_reference="Test source",
            )
            assert pattern.category == category

    def test_risk_level_in_validation(self):
        """Test that RiskLevel can be used in validation logic."""
        from apps.abstraction.domain.services import AbstractionRuleValidator
        from apps.abstraction.domain.entities import AbstractionRule

        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.FORM,
            observation="Safe observation",
            applied_rule="Safe rule",
        )

        # Test all risk levels
        for risk_level in list(RiskLevel):
            # Should not raise any errors
            is_valid, reason = AbstractionRuleValidator.validate_rule(
                rule,
                license_risk=risk_level
            )
            assert isinstance(is_valid, bool)
            assert isinstance(reason, (str, type(None)))
