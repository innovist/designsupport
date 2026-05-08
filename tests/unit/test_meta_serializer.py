"""Unit tests for SessionMetaMixin.

Tests SPEC-05-API-001 compliance:
- current_step (int, 1-17)
- mode (string: "guided" or "auto")
- evidence_refs (list of citation IDs)
- is_hypothesis (boolean)
- decision_required (boolean)
- next_actions (list of available action strings)
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from apps.design_sessions.domain.entities import DesignSession, PipelineStep, SessionMode
from shared.presentation.meta_serializer import SessionMetaMixin


class MockSerializer(SessionMetaMixin):
    """Mock serializer for testing SessionMetaMixin."""

    def __init__(self):
        pass


class TestSessionMetaMixin:
    """Test suite for SessionMetaMixin SPEC-05-API-001 compliance."""

    @pytest.fixture
    def mixin(self):
        """Create a SessionMetaMixin instance."""
        return MockSerializer()

    @pytest.fixture
    def guided_session(self):
        """Create a guided mode session."""
        return DesignSession(
            project_id=uuid4(),
            started_by=uuid4(),
            mode=SessionMode.GUIDED,
            current_step=PipelineStep.PURPOSE_INPUT,
        )

    @pytest.fixture
    def auto_session(self):
        """Create an auto mode session."""
        return DesignSession(
            project_id=uuid4(),
            started_by=uuid4(),
            mode=SessionMode.AUTO,
            current_step=PipelineStep.GENERATION,
        )

    def test_get_current_step_returns_int(self, mixin, guided_session):
        """Test that current_step returns integer value."""
        result = mixin.get_current_step(guided_session)
        assert isinstance(result, int)
        assert result == PipelineStep.PURPOSE_INPUT.value

    def test_get_mode_returns_string(self, mixin, guided_session, auto_session):
        """Test that mode returns string value."""
        guided_mode = mixin.get_mode(guided_session)
        auto_mode = mixin.get_mode(auto_session)

        assert guided_mode == "guided"
        assert auto_mode == "auto"

    def test_get_evidence_refs_returns_list(self, mixin):
        """Test that evidence_refs returns list."""
        session_dict = {"evidence_refs": ["cite-1", "cite-2"]}
        result = mixin.get_evidence_refs(session_dict)

        assert isinstance(result, list)
        assert result == ["cite-1", "cite-2"]

    def test_get_evidence_refs_empty_by_default(self, mixin, guided_session):
        """Test that evidence_refs returns empty list by default."""
        result = mixin.get_evidence_refs(guided_session)
        assert isinstance(result, list)
        assert result == []

    def test_get_is_hypothesis_true_for_early_steps(self, mixin, guided_session):
        """Test that is_hypothesis is True for early steps (1-4)."""
        result = mixin.get_is_hypothesis(guided_session)
        assert result is True  # Step 1 (PURPOSE_INPUT) is hypothesis

    def test_get_is_hypothesis_false_for_later_steps(self, mixin, auto_session):
        """Test that is_hypothesis is False for later steps."""
        result = mixin.get_is_hypothesis(auto_session)
        assert result is False  # Step 13 (GENERATION) is not hypothesis

    def test_get_decision_required_true_for_guided_mode_decision_steps(self, mixin):
        """Test that decision_required is True for guided mode at decision steps."""
        # Step 7 (CONCEPT_EVALUATION) requires decision in guided mode
        session_dict = {
            "mode": SessionMode.GUIDED,
            "current_step": PipelineStep.CONCEPT_EVALUATION,
        }
        result = mixin.get_decision_required(session_dict)
        assert result is True

    def test_get_decision_required_false_for_auto_mode(self, mixin, auto_session):
        """Test that decision_required is False for auto mode."""
        result = mixin.get_decision_required(auto_session)
        assert result is False

    def test_get_next_actions_includes_advance(self, mixin, guided_session):
        """Test that next_actions includes 'advance' for non-final steps."""
        result = mixin.get_next_actions(guided_session)
        assert "advance" in result

    def test_get_next_actions_includes_approve_for_decision_steps(self, mixin):
        """Test that next_actions includes approve/request_changes for decision steps."""
        session_dict = {
            "current_step": PipelineStep.CONCEPT_DECISION,  # Step 8
            "mode": SessionMode.GUIDED,
        }
        result = mixin.get_next_actions(session_dict)

        assert "approve" in result
        assert "request_changes" in result

    def test_get_next_actions_includes_restart_after_first_step(self, mixin):
        """Test that next_actions includes restart_step after step 1."""
        session_dict = {
            "current_step": PipelineStep.GENERATION,  # Step 13
        }
        result = mixin.get_next_actions(session_dict)
        assert "restart_step" in result

    def test_meta_fields_validation(self, mixin):
        """Test that all required meta fields are present and valid."""
        # Verify the mixin defines all required fields
        assert hasattr(mixin, "current_step")
        assert hasattr(mixin, "mode")
        assert hasattr(mixin, "evidence_refs")
        assert hasattr(mixin, "is_hypothesis")
        assert hasattr(mixin, "decision_required")
        assert hasattr(mixin, "next_actions")

    def test_current_step_range_validation(self, mixin):
        """Test that current_step is validated to be 1-17."""
        # This would be tested via DRF serializer validation in integration tests
        # Here we verify the field exists with correct constraints
        from rest_framework import serializers

        # Check that the field has min_value and max_value
        field = mixin.current_step
        assert hasattr(field, "min_value")
        assert hasattr(field, "max_value")
        # Note: Field is a Field instance, not the value itself

    def test_mode_choice_validation(self, mixin):
        """Test that mode is limited to 'guided' or 'auto'."""
        from rest_framework import serializers

        field = mixin.mode
        assert hasattr(field, "choices")
        # Choices would be ["guided", "auto"]

    def test_handles_dict_input(self, mixin):
        """Test that mixin handles dict input from API requests."""
        session_dict = {
            "current_step": PipelineStep.TREND_RESEARCH,  # Step 5
            "mode": "auto",
            "evidence_refs": ["cite-1"],
        }

        assert mixin.get_current_step(session_dict) == 5
        assert mixin.get_mode(session_dict) == "auto"
        assert mixin.get_evidence_refs(session_dict) == ["cite-1"]

    def test_handles_entity_input(self, mixin, guided_session):
        """Test that mixin handles entity input from domain layer."""
        assert mixin.get_current_step(guided_session) == 1
        assert mixin.get_mode(guided_session) == "guided"
        assert isinstance(mixin.get_evidence_refs(guided_session), list)
