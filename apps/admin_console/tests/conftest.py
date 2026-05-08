"""Pytest fixtures for admin_console module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for admin_console tests."""
    return {"test": "data"}
