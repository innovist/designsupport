"""Application ports for accounts module.

Defines interfaces for external dependencies following Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from apps.accounts.domain.entities import User


# @MX:ANCHOR: [AUTO] User repository port - data access abstraction
# @MX:REASON: High fan_in - implemented by repository, used by all account use cases
class UserRepositoryPort(ABC):
    """Repository port for User aggregate."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email address

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save user (create or update).

        Args:
            user: User entity to save

        Returns:
            Saved user entity
        """
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        pass


# @MX:ANCHOR: [AUTO] Authentication service port - security operations abstraction
# @MX:REASON: High fan_in - implemented by infrastructure, used by auth use cases
class AuthServicePort(ABC):
    """Service port for authentication operations."""

    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """Hash password using Argon2id.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        pass

    @abstractmethod
    async def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash.

        Args:
            password: Plain text password
            password_hash: Hashed password to verify against

        Returns:
            True if password matches hash, False otherwise
        """
        pass

    @abstractmethod
    async def create_token(self, user_id: UUID) -> str:
        """Create JWT access token for user.

        Args:
            user_id: User UUID

        Returns:
            JWT token string
        """
        pass
