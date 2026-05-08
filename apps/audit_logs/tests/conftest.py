"""Pytest fixtures for audit_logs module."""
import pytest


@pytest.fixture
def sample_data():
    """Sample data fixture for audit_logs tests."""
    return {"test": "data"}
