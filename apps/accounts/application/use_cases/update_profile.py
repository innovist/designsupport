"""Update profile use case.

Updates user profile information.
"""
from uuid import UUID

from apps.accounts.application.dtos import UpdateProfileRequest, UserDTO
from apps.accounts.application.ports import UserRepositoryPort
from shared.application.decorators.audit import audit
from shared.application.result import Result


@audit(
    "accounts.update_profile",
    target_type_extractor=lambda **kw: "User",
    target_id_extractor=lambda **kw: str(kw.get("user_id", "")),
    record_failures=False,
)
class UpdateProfileUseCase:
    """Use case for updating user profile."""

    def __init__(self, user_repository: UserRepositoryPort):
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
        """
        self._user_repository = user_repository

    async def execute(
        self,
        user_id: UUID,
        request: UpdateProfileRequest,
    ) -> Result[UserDTO]:
        """Execute profile update.

        Args:
            user_id: User UUID
            request: Update request with optional fields

        Returns:
            Result containing updated UserDTO on success,
            Result with error on user not found
        """
        user = await self._user_repository.get_by_id(user_id)

        if user is None:
            from shared.domain.exceptions import NotFoundError

            return Result.failure(NotFoundError('User not found'))

        # Update user entity
        if request.display_name is not None:
            user.display_name = request.display_name

        if request.default_workspace_id is not None:
            user.set_default_workspace(request.default_workspace_id)

        # Save changes
        updated_user = await self._user_repository.save(user)

        # Convert to DTO
        user_dto = UserDTO(
            id=updated_user.id,
            email=updated_user.email,
            display_name=updated_user.display_name,
            default_workspace_id=updated_user.default_workspace_id,
            is_active=updated_user.is_active,
        )

        return Result.success(user_dto)
