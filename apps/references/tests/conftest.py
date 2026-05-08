"""Pytest fixtures for references module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for references tests."""
    return {"test": "data"}
