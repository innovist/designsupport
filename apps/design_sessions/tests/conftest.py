"""Pytest fixtures for design_sessions module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for design_sessions tests."""
    return {"test": "data"}
