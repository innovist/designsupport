"""Pytest fixtures for user_assets module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for user_assets tests."""
    return {"test": "data"}
