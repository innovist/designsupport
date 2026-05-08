"""Django ORM repository implementation for User aggregate.

Implements UserRepositoryPort using Django ORM for persistence.
"""
from typing import Optional
from uuid import UUID

from asgiref.sync import sync_to_async

from apps.accounts.application.ports import UserRepositoryPort
from apps.accounts.domain.entities import User
from apps.accounts.infrastructure.orm.models import UserModel


class DjangoUserRepository(UserRepositoryPort):
    """Django ORM implementation of UserRepositoryPort.

    Converts between domain entities and Django ORM models.
    """

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email address

        Returns:
            User entity if found, None otherwise
        """
        try:
            model = await UserModel.objects.aget(email=email)
            return self._model_to_entity(model)
        except UserModel.DoesNotExist:
            return None

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User entity if found, None otherwise
        """
        try:
            model = await UserModel.objects.aget(id=user_id)
            return self._model_to_entity(model)
        except UserModel.DoesNotExist:
            return None

    async def save(self, user: User) -> User:
        """Save user (create or update).

        Args:
            user: User entity to save

        Returns:
            Saved user entity with updated timestamp
        """
        # Check if this is a create or update
        model_exists = await UserModel.objects.filter(id=user.id).aexists()

        if model_exists:
            # Update existing
            model = await UserModel.objects.aget(id=user.id)
            model.display_name = user.display_name
            model.default_workspace_id = user.default_workspace_id
            model.is_active = user.is_active
            # Never update password_hash through save() - use dedicated method
            # Never update email through save() - email is immutable
            await sync_to_async(model.save)()
        else:
            # Create new
            model = await UserModel.objects.acreate(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                display_name=user.display_name,
                default_workspace_id=user.default_workspace_id,
                is_active=user.is_active,
            )

        await sync_to_async(model.refresh_from_db)()
        return self._model_to_entity(model)

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        return await UserModel.objects.filter(email=email).aexists()

    def _model_to_entity(self, model: UserModel) -> User:
        """Convert Django ORM model to domain entity.

        Args:
            model: UserModel instance

        Returns:
            User domain entity
        """
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            display_name=model.display_name,
            default_workspace_id=model.default_workspace_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
