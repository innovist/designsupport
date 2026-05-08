"""Register user use case.

Handles user registration with email uniqueness validation and password hashing.
"""
from uuid import UUID

from apps.accounts.application.dtos import RegisterRequest, RegisterResponse, UserDTO
from apps.accounts.application.ports import AuthServicePort, UserRepositoryPort
from apps.accounts.domain.entities import User
from apps.accounts.domain.invariants import UserInvariantViolationError, validate_email_format
from shared.application.decorators.audit import audit
from shared.application.result import Result


# @MX:ANCHOR: [AUTO] User registration use case - creates new accounts
# @MX:REASON: High fan_in - called by RegisterView, tests, admin operations
@audit(
    "accounts.register",
    target_type_extractor=lambda **kw: "User",
    target_id_extractor=lambda **kw: "",
    record_failures=False,
)
class RegisterUserUseCase:
    """Use case for registering new users.

    Validates email uniqueness, hashes password, creates user entity,
    and returns user with authentication token.
    """

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        auth_service: AuthServicePort,
    ):
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            auth_service: Service for password hashing and token creation
        """
        self._user_repository = user_repository
        self._auth_service = auth_service

    # @MX:ANCHOR: [AUTO] Registration execution - email validation, password hashing, user creation
    # @MX:REASON: High fan_in - called by API view, test suites, seed scripts
    async def execute(self, request: RegisterRequest) -> Result[RegisterResponse]:
        """Execute user registration.

        Args:
            request: Registration request with email, password, display_name

        Returns:
            Result containing RegisterResponse on success,
            Result with error on validation or persistence failure
        """
        # Validate email format
        try:
            validate_email_format(request.email)
        except UserInvariantViolationError as exc:
            from shared.domain.exceptions import ValidationError
            return Result.failure(ValidationError('email', str(exc)))

        # Check email uniqueness
        existing = await self._user_repository.get_by_email(request.email)
        if existing is not None:
            from shared.domain.exceptions import ValidationError

            return Result.failure(
                ValidationError(
                    'email',
                    'User with this email already exists'
                )
            )

        # Hash password
        password_hash = await self._auth_service.hash_password(request.password)

        # Create user entity
        user = User(
            email=request.email,
            password_hash=password_hash,
            display_name=request.display_name,
        )

        # Persist user
        saved_user = await self._user_repository.save(user)

        # Create authentication token
        token = await self._auth_service.create_token(saved_user.id)

        # Return response
        user_dto = UserDTO(
            id=saved_user.id,
            email=saved_user.email,
            display_name=saved_user.display_name,
            default_workspace_id=saved_user.default_workspace_id,
            is_active=saved_user.is_active,
        )

        return Result.success(RegisterResponse(user=user_dto, token=token))
