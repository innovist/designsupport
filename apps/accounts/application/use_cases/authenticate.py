"""Authenticate user use case.

Handles user authentication with credential validation and token generation.
"""
from apps.accounts.application.dtos import LoginRequest, LoginResponse, UserDTO
from apps.accounts.application.ports import AuthServicePort, UserRepositoryPort
from shared.application.decorators.audit import audit
from shared.application.result import Result


@audit(
    "accounts.authenticate",
    target_type_extractor=lambda **kw: "User",
    target_id_extractor=lambda **kw: str(kw.get("request", {}) and getattr(kw.get("request"), "email", "")),
    record_failures=False,
)
class AuthenticateUseCase:
    """Use case for user authentication.

    Validates user credentials, verifies password, and returns
    user data with authentication token.
    """

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        auth_service: AuthServicePort,
    ):
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user lookup
            auth_service: Service for password verification and token creation
        """
        self._user_repository = user_repository
        self._auth_service = auth_service

    async def execute(self, request: LoginRequest) -> Result[LoginResponse]:
        """Execute user authentication.

        Args:
            request: Login request with email and password

        Returns:
            Result containing LoginResponse with user and token on success,
            Result with error on invalid credentials or inactive user
        """
        # Look up user by email
        user = await self._user_repository.get_by_email(request.email)

        if user is None:
            from shared.domain.exceptions import PermissionDeniedError

            return Result.failure(
                PermissionDeniedError('Invalid email or password')
            )

        # Verify password
        password_valid = await self._auth_service.verify_password(
            request.password,
            user.password_hash,
        )

        if not password_valid:
            from shared.domain.exceptions import PermissionDeniedError

            return Result.failure(
                PermissionDeniedError('Invalid email or password')
            )

        # Check if user is active
        if not user.is_active:
            from shared.domain.exceptions import PermissionDeniedError

            return Result.failure(
                PermissionDeniedError('User account is inactive')
            )

        # Create authentication token
        token = await self._auth_service.create_token(user.id)

        # Return response
        user_dto = UserDTO(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            default_workspace_id=user.default_workspace_id,
            is_active=user.is_active,
        )

        return Result.success(LoginResponse(user=user_dto, token=token))
