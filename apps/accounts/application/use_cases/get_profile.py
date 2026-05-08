"""Get profile use case.

Retrieves user profile by user ID.
"""
from typing import Optional
from uuid import UUID

from apps.accounts.application.dtos import UserDTO
from apps.accounts.application.ports import UserRepositoryPort
from shared.application.result import Result


class GetProfileUseCase:
    """Use case for retrieving user profile."""

    def __init__(self, user_repository: UserRepositoryPort):
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user lookup
        """
        self._user_repository = user_repository

    async def execute(self, user_id: UUID) -> Result[UserDTO]:
        """Execute profile retrieval.

        Args:
            user_id: User UUID

        Returns:
            Result containing UserDTO on success,
            Result with error on user not found
        """
        user = await self._user_repository.get_by_id(user_id)

        if user is None:
            from shared.domain.exceptions import NotFoundError

            return Result.failure(NotFoundError('User not found'))

        user_dto = UserDTO(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            default_workspace_id=user.default_workspace_id,
            is_active=user.is_active,
        )

        return Result.success(user_dto)
