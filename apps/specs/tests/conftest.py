"""Pytest fixtures for specs module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for specs tests."""
    return {"test": "data"}
