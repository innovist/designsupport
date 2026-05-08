"""Tests for generation domain entities."""
import pytest
from uuid import uuid4

from apps.generation.domain.entities import GenerationJob, GeneratedDesign, CostMetadata
from apps.generation.domain.value_objects import (
    GenerationStatus,
    GenerationKind,
    AssetKind
)
from shared.domain.exceptions import ValidationError


class TestCostMetadata:
    """Test CostMetadata value object."""

    def test_create_cost_metadata(self):
        """Test creating valid cost metadata."""
        cost = CostMetadata(
            model_key="seedream-4.5",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.003
        )

        assert cost.model_key == "seedream-4.5"
        assert cost.prompt_tokens == 100
        assert cost.completion_tokens == 50
        assert cost.total_tokens == 150
        assert cost.cost_usd == 0.003

    def test_cost_metadata_negative_values_fail(self):
        """Test that negative values fail validation."""
        with pytest.raises(ValidationError):
            CostMetadata(
                model_key="seedream-4.5",
                prompt_tokens=-100,
                completion_tokens=50,
                total_tokens=150,
                cost_usd=0.003
            )


class TestGenerationJob:
    """Test GenerationJob entity."""

    def test_create_sketch_job(self):
        """Test creating a sketch generation job."""
        job = GenerationJob(
            session_id=uuid4(),
            kind=GenerationKind.SKETCH,
            brief_id=uuid4(),
            concept_id=uuid4(),
            model_policy_key="default"
        )

        assert job.status == GenerationStatus.QUEUED
        assert job.kind == GenerationKind.SKETCH
        assert job.retries == 0

    def test_create_refinement_job_requires_sketch(self):
        """Test that refinement jobs require a parent sketch."""
        with pytest.raises(ValidationError):
            GenerationJob(
                session_id=uuid4(),
                kind=GenerationKind.REFINEMENT,
                brief_id=uuid4(),
                model_policy_key="default"
            )

    def test_create_variation_job_requires_rules(self):
        """Test that variation jobs require abstraction rules."""
        with pytest.raises(ValidationError):
            GenerationJob(
                session_id=uuid4(),
                kind=GenerationKind.VARIATION,
                brief_id=uuid4(),
                model_policy_key="default"
            )

    def test_job_must_link_to_context(self):
        """Test REQ-03-GEN-002: Job must link to at least one context."""
        with pytest.raises(ValidationError):
            GenerationJob(
                session_id=uuid4(),
                kind=GenerationKind.SKETCH,
                model_policy_key="default"
            )

    def test_job_status_transition(self):
        """Test valid status transitions."""
        job = GenerationJob(
            session_id=uuid4(),
            kind=GenerationKind.SKETCH,
            brief_id=uuid4(),
            model_policy_key="default"
        )

        # Valid transition: queued -> running
        job.transition_to(GenerationStatus.RUNNING)
        assert job.status == GenerationStatus.RUNNING

        # Valid transition: running -> completed
        job.transition_to(GenerationStatus.COMPLETED)
        assert job.status == GenerationStatus.COMPLETED
        assert job.completed_at is not None

    def test_invalid_status_transition_fails(self):
        """Test that invalid status transitions fail."""
        job = GenerationJob(
            session_id=uuid4(),
            kind=GenerationKind.SKETCH,
            brief_id=uuid4(),
            model_policy_key="default"
        )

        # Invalid transition: queued -> completed (must go through running)
        with pytest.raises(ValidationError):
            job.transition_to(GenerationStatus.COMPLETED)

    def test_job_retry(self):
        """Test job retry mechanism."""
        job = GenerationJob(
            session_id=uuid4(),
            kind=GenerationKind.SKETCH,
            brief_id=uuid4(),
            model_policy_key="default"
        )

        # Mark as failed
        job.transition_to(GenerationStatus.FAILED, error="Test error")
        assert job.status == GenerationStatus.FAILED
        assert job.error_message == "Test error"

        # Retry
        job.increment_retry()
        assert job.status == GenerationStatus.QUEUED
        assert job.retries == 1
        assert job.error_message is None


class TestGeneratedDesign:
    """Test GeneratedDesign entity."""

    def test_create_generated_design(self):
        """Test creating a generated design."""
        design = GeneratedDesign(
            job_id=uuid4(),
            asset_uri="https://example.com/image.png",
            asset_kind=AssetKind.IMAGE,
            brief_id=uuid4(),
            model_policy_key="seedream-4.5"
        )

        assert design.asset_uri == "https://example.com/image.png"
        assert design.asset_kind == AssetKind.IMAGE

    def test_design_requires_asset_uri(self):
        """Test that design requires asset URI."""
        with pytest.raises(ValidationError):
            GeneratedDesign(
                job_id=uuid4(),
                asset_uri="",
                asset_kind=AssetKind.IMAGE,
                brief_id=uuid4(),
                model_policy_key="seedream-4.5"
            )
