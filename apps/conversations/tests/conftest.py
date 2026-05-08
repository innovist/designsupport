"""Pytest fixtures for conversations module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for conversations tests."""
    return {"test": "data"}
