"""Pytest fixtures for model_catalog module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for model_catalog tests."""
    return {"test": "data"}
