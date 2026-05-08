"""Pytest fixtures for accounts module."""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user_factory(db):
    """Factory for creating test users."""
    def create_user(
        email: str = "test@example.com",
        password: str = "testpass123",
        **kwargs,
    ):
        return User.objects.create_user(
            email=email,
            password=password,
            **kwargs,
        )
    return create_user


@pytest.fixture
def test_user(user_factory):
    """Create a test user."""
    return user_factory(email="testuser@example.com")
