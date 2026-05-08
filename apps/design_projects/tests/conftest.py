"""Pytest fixtures for design_projects module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for design_projects tests."""
    return {"test": "data"}
