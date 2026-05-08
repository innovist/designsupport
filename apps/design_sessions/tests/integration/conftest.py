"""Pytest configuration for design_sessions integration tests."""
import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.django_db)
