"""Unit tests for abstraction domain entities.

Tests cover validation, risk marking, and business invariants.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from apps.abstraction.domain.entities import (
    AbstractionRule,
    SketchPrompt,
    PromptPattern,
    PromptSafetyViolation,
)
from apps.abstraction.domain.value_objects import (
    AbstractionAxis,
    SketchPromptKind,
    PromptCategory,
)
from shared.domain.exceptions import ValidationError


class TestAbstractionRule:
    """Test AbstractionRule entity."""

    def test_valid_creation_with_required_fields(self):
        """Test creating a valid AbstractionRule."""
        session_id = uuid4()
        concept_id = uuid4()

        rule = AbstractionRule(
            session_id=session_id,
            concept_id=concept_id,
            axis=AbstractionAxis.FORM,
            observation="The concept uses geometric shapes",
            applied_rule="Use geometric primitives to define form structure",
        )

        assert rule.id is not None
        assert isinstance(rule.id, UUID)
        assert rule.session_id == session_id
        assert rule.concept_id == concept_id
        assert rule.axis == AbstractionAxis.FORM
        assert rule.observation == "The concept uses geometric shapes"
        assert rule.applied_rule == "Use geometric primitives to define form structure"
        assert rule.source_refs == []
        assert rule.risk_note is None
        assert rule.created_at is not None

    def test_valid_creation_with_optional_fields(self):
        """Test creating rule with optional fields."""
        source_ref_1 = uuid4()
        source_ref_2 = uuid4()

        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.SURFACE,
            observation="Matte finish with subtle texture",
            applied_rule="Apply matte finish with tactile texture",
            source_refs=[source_ref_1, source_ref_2],
            risk_note=None,
        )

        assert len(rule.source_refs) == 2
        assert source_ref_1 in rule.source_refs
        assert source_ref_2 in rule.source_refs

    def test_valid_all_six_axes(self):
        """Test that all six abstraction axes are valid."""
        session_id = uuid4()
        concept_id = uuid4()

        for axis in AbstractionAxis.all_axes():
            rule = AbstractionRule(
                session_id=session_id,
                concept_id=concept_id,
                axis=axis,
                observation=f"Observation for {axis.value}",
                applied_rule=f"Rule for {axis.value}",
            )
            assert rule.axis == axis

    def test_empty_observation_raises_error(self):
        """Test that empty observation raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AbstractionRule(
                session_id=uuid4(),
                concept_id=uuid4(),
                axis=AbstractionAxis.FORM,
                observation="",  # Empty
                applied_rule="Valid rule",
            )

        assert exc_info.value.field == "observation"
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_whitespace_only_observation_raises_error(self):
        """Test that whitespace-only observation raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AbstractionRule(
                session_id=uuid4(),
                concept_id=uuid4(),
                axis=AbstractionAxis.MEANING,
                observation="   ",  # Whitespace only
                applied_rule="Valid rule",
            )

        assert exc_info.value.field == "observation"

    def test_empty_applied_rule_raises_error(self):
        """Test that empty applied_rule raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AbstractionRule(
                session_id=uuid4(),
                concept_id=uuid4(),
                axis=AbstractionAxis.STRUCTURE,
                observation="Valid observation",
                applied_rule="",  # Empty
            )

        assert exc_info.value.field == "applied_rule"
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_invalid_axis_raises_error(self):
        """Test that invalid axis raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AbstractionRule(
                session_id=uuid4(),
                concept_id=uuid4(),
                axis="invalid_axis",  # Not in enum
                observation="Valid observation",
                applied_rule="Valid rule",
            )

        assert exc_info.value.field == "axis"
        assert "Invalid axis" in str(exc_info.value)

    def test_mark_risky_adds_risk_note(self):
        """Test that mark_risky adds risk note."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.COLOR_MATERIAL,
            observation="Blue color scheme",
            applied_rule="Use blue color palette",
        )

        assert rule.risk_note is None

        rule.mark_risky("Mimics Coca-Cola brand color scheme")

        assert rule.risk_note == "Mimics Coca-Cola brand color scheme"

    def test_mark_risky_overwrites_existing_note(self):
        """Test that mark_risky overwrites existing risk note."""
        rule = AbstractionRule(
            session_id=uuid4(),
            concept_id=uuid4(),
            axis=AbstractionAxis.USABILITY,
            observation="Simple button layout",
            applied_rule="Use simple button layout",
            risk_note="Old risk note",
        )

        rule.mark_risky("New risk note: mimics Apple UI")

        assert rule.risk_note == "New risk note: mimics Apple UI"


class TestSketchPrompt:
    """Test SketchPrompt entity."""

    def test_valid_creation_preserve_original(self):
        """Test creating preserve_original prompt."""
        session_id = uuid4()

        prompt = SketchPrompt(
            session_id=session_id,
            kind=SketchPromptKind.PRESERVE_ORIGINAL,
            template="Generate a sketch with {elements}",
            variables={"elements": "geometric shapes"},
        )

        assert prompt.id is not None
        assert prompt.session_id == session_id
        assert prompt.kind == SketchPromptKind.PRESERVE_ORIGINAL
        assert prompt.template == "Generate a sketch with {elements}"
        assert prompt.variables == {"elements": "geometric shapes"}
        assert prompt.source_refs == []

    def test_valid_creation_expand_concept(self):
        """Test creating expand_concept prompt."""
        session_id = uuid4()

        prompt = SketchPrompt(
            session_id=session_id,
            kind=SketchPromptKind.EXPAND_CONCEPT,
            template="Expand the concept by exploring {directions}",
            variables={"directions": "minimalist forms"},
        )

        assert prompt.kind == SketchPromptKind.EXPAND_CONCEPT

    def test_empty_template_raises_error(self):
        """Test that empty template raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SketchPrompt(
                session_id=uuid4(),
                kind=SketchPromptKind.PRESERVE_ORIGINAL,
                template="",  # Empty
                variables={},
            )

        assert exc_info.value.field == "template"
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_invalid_kind_raises_error(self):
        """Test that invalid kind raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SketchPrompt(
                session_id=uuid4(),
                kind="invalid_kind",  # Not in enum
                template="Valid template",
                variables={},
            )

        assert exc_info.value.field == "kind"
        assert "Invalid kind" in str(exc_info.value)

    def test_render_substitutes_variables(self):
        """Test that render substitutes variables into template."""
        prompt = SketchPrompt(
            session_id=uuid4(),
            kind=SketchPromptKind.PRESERVE_ORIGINAL,
            template="Create a sketch with {style} and {elements}",
            variables={
                "style": "minimalist",
                "elements": "geometric shapes",
            },
        )

        rendered = prompt.render()

        assert rendered == "Create a sketch with minimalist and geometric shapes"

    def test_render_with_missing_variable(self):
        """Test render with missing variable leaves placeholder."""
        prompt = SketchPrompt(
            session_id=uuid4(),
            kind=SketchPromptKind.PRESERVE_ORIGINAL,
            template="Create a sketch with {style} and {missing}",
            variables={"style": "minimalist"},
        )

        rendered = prompt.render()

        assert rendered == "Create a sketch with minimalist and {missing}"

    def test_render_with_no_variables(self):
        """Test render with no variables returns template unchanged."""
        prompt = SketchPrompt(
            session_id=uuid4(),
            kind=SketchPromptKind.EXPAND_CONCEPT,
            template="Create a minimalist sketch",
            variables={},
        )

        rendered = prompt.render()

        assert rendered == "Create a minimalist sketch"


class TestPromptPattern:
    """Test PromptPattern entity."""

    def test_valid_creation_with_all_fields(self):
        """Test creating a valid PromptPattern."""
        pattern = PromptPattern(
            name="Line to Render Conversion",
            category=PromptCategory.LINE_TO_RENDER,
            source_reference="WGSN Trend Report 2026",
            input_slots=["line_art", "style_reference"],
            output_constraints=["photorealistic", "consistent lighting"],
            safety_rules=["No brand logos", "No trademarked elements"],
            domain_tags=["fashion", "sketch"],
        )

        assert pattern.id is not None
        assert pattern.name == "Line to Render Conversion"
        assert pattern.category == PromptCategory.LINE_TO_RENDER
        assert pattern.active is True
        assert len(pattern.input_slots) == 2
        assert len(pattern.safety_rules) == 2

    def test_valid_creation_with_minimum_fields(self):
        """Test creating pattern with only required fields."""
        pattern = PromptPattern(
            name="Test Pattern",
            category=PromptCategory.STORYBOARD,
            source_reference="Test source",
        )

        assert pattern.input_slots == []
        assert pattern.output_constraints == []
        assert pattern.safety_rules == []
        assert pattern.domain_tags == []
        assert pattern.active is True

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptPattern(
                name="",  # Empty
                category=PromptCategory.MOODBOARD_COLLAGE,
                source_reference="Valid source",
            )

        assert exc_info.value.field == "name"
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_empty_source_reference_raises_error(self):
        """Test that empty source_reference raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptPattern(
                name="Valid name",
                category=PromptCategory.DIAGRAM_ANNOTATION,
                source_reference="",  # Empty
            )

        assert exc_info.value.field == "source_reference"
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_invalid_category_raises_error(self):
        """Test that invalid category raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptPattern(
                name="Valid name",
                category="invalid_category",  # Not in enum
                source_reference="Valid source",
            )

        assert exc_info.value.field == "category"
        assert "Invalid category" in str(exc_info.value)

    def test_deactivate_sets_active_false(self):
        """Test that deactivate sets active to False."""
        pattern = PromptPattern(
            name="Test Pattern",
            category=PromptCategory.PRODUCT_PACKAGING,
            source_reference="Test source",
            active=True,
        )

        original_updated_at = pattern.updated_at
        pattern.deactivate()

        assert pattern.active is False
        assert pattern.updated_at > original_updated_at

    def test_activate_sets_active_true(self):
        """Test that activate sets active to True."""
        pattern = PromptPattern(
            name="Test Pattern",
            category=PromptCategory.MATERIAL_TEXTURE,
            source_reference="Test source",
            active=False,
        )

        original_updated_at = pattern.updated_at
        pattern.activate()

        assert pattern.active is True
        assert pattern.updated_at > original_updated_at

    def test_all_ten_categories_valid(self):
        """Test that all ten prompt categories are valid."""
        valid_categories = [
            PromptCategory.LINE_TO_RENDER,
            PromptCategory.MULTI_REFERENCE_FUSION,
            PromptCategory.PRODUCT_PACKAGING,
            PromptCategory.MATERIAL_TEXTURE,
            PromptCategory.EXPLODED_VIEW,
            PromptCategory.STORYBOARD,
            PromptCategory.MOODBOARD_COLLAGE,
            PromptCategory.DIAGRAM_ANNOTATION,
            PromptCategory.DOMAIN_APPLICATION,
            PromptCategory.REFINEMENT_PRESERVE_ORIGINAL,
        ]

        for category in valid_categories:
            pattern = PromptPattern(
                name=f"Pattern for {category.value}",
                category=category,
                source_reference="Test source",
            )
            assert pattern.category == category


class TestPromptSafetyViolation:
    """Test PromptSafetyViolation entity."""

    def test_valid_creation_with_prompt_id(self):
        """Test creating violation with prompt_id."""
        session_id = uuid4()
        prompt_id = uuid4()

        violation = PromptSafetyViolation(
            session_id=session_id,
            prompt_id=prompt_id,
            reason="Violates safety rule: mimics brand style",
        )

        assert violation.id is not None
        assert violation.session_id == session_id
        assert violation.prompt_id == prompt_id
        assert violation.reason == "Violates safety rule: mimics brand style"
        assert violation.source_refs == []

    def test_valid_creation_without_prompt_id(self):
        """Test creating violation without prompt_id."""
        session_id = uuid4()

        violation = PromptSafetyViolation(
            session_id=session_id,
            prompt_id=None,
            reason="General safety violation detected",
        )

        assert violation.prompt_id is None
        assert violation.reason == "General safety violation detected"

    def test_valid_creation_with_source_refs(self):
        """Test creating violation with source references."""
        source_ref_1 = uuid4()
        source_ref_2 = uuid4()

        violation = PromptSafetyViolation(
            session_id=uuid4(),
            prompt_id=uuid4(),
            reason="Multiple safety violations",
            source_refs=[source_ref_1, source_ref_2],
        )

        assert len(violation.source_refs) == 2
        assert source_ref_1 in violation.source_refs
        assert source_ref_2 in violation.source_refs

    def test_empty_reason_raises_error(self):
        """Test that empty reason raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptSafetyViolation(
                session_id=uuid4(),
                prompt_id=uuid4(),
                reason="",  # Empty
            )

        assert exc_info.value.field == "reason"
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_whitespace_only_reason_raises_error(self):
        """Test that whitespace-only reason raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PromptSafetyViolation(
                session_id=uuid4(),
                prompt_id=uuid4(),
                reason="   ",  # Whitespace only
            )

        assert exc_info.value.field == "reason"
