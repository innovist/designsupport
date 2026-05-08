"""Pytest fixtures for abstraction module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for abstraction tests."""
    return {"test": "data"}
