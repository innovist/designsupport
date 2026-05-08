"""Pytest fixtures for concepts module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for concepts tests."""
    return {"test": "data"}
