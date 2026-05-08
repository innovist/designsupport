"""Dependency injection container for accounts module.

Provides factory methods for creating use cases with their dependencies.
This keeps the presentation layer decoupled from infrastructure implementations.
"""
from apps.accounts.application.use_cases.authenticate import AuthenticateUseCase
from apps.accounts.application.use_cases.get_profile import GetProfileUseCase
from apps.accounts.application.use_cases.register_user import RegisterUserUseCase
from apps.accounts.application.use_cases.update_profile import UpdateProfileUseCase
from apps.accounts.application.ports import AuthServicePort, UserRepositoryPort
from apps.accounts.infrastructure.adapters.auth_adapter import DjangoAuthService
from apps.accounts.infrastructure.repositories.user_repository import DjangoUserRepository


class AccountsContainer:
    """Dependency injection container for accounts module.

    Provides factory methods to create fully-wired use cases.
    This isolates the presentation layer from infrastructure details.
    """

    def __init__(self):
        """Initialize container with shared dependencies."""
        self._user_repository: UserRepositoryPort = DjangoUserRepository()
        self._auth_service: AuthServicePort = DjangoAuthService()

    def register_user(self) -> RegisterUserUseCase:
        """Create RegisterUserUseCase with dependencies.

        Returns:
            Wired RegisterUserUseCase instance
        """
        return RegisterUserUseCase(
            user_repository=self._user_repository,
            auth_service=self._auth_service,
        )

    def authenticate(self) -> AuthenticateUseCase:
        """Create AuthenticateUseCase with dependencies.

        Returns:
            Wired AuthenticateUseCase instance
        """
        return AuthenticateUseCase(
            user_repository=self._user_repository,
            auth_service=self._auth_service,
        )

    def get_profile(self) -> GetProfileUseCase:
        """Create GetProfileUseCase with dependencies.

        Returns:
            Wired GetProfileUseCase instance
        """
        return GetProfileUseCase(user_repository=self._user_repository)

    def update_profile(self) -> UpdateProfileUseCase:
        """Create UpdateProfileUseCase with dependencies.

        Returns:
            Wired UpdateProfileUseCase instance
        """
        return UpdateProfileUseCase(user_repository=self._user_repository)
