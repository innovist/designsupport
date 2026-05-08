"""Pytest fixtures for generation module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for generation tests."""
    return {"test": "data"}
