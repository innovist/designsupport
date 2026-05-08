"""Pytest fixtures for workspaces module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for workspaces tests."""
    return {"test": "data"}
