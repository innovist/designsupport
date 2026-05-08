"""DRF serializers for accounts module.

Defines request/response serializers for API endpoints.
"""
from rest_framework import serializers

from apps.accounts.application.dtos import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UpdateProfileRequest,
    UserDTO,
)


class UserSerializer(serializers.Serializer):
    """Serializer for UserDTO."""

    id = serializers.UUIDField()
    email = serializers.EmailField()
    display_name = serializers.CharField()
    default_workspace_id = serializers.UUIDField(allow_null=True)
    is_active = serializers.BooleanField()


class LoginSerializer(serializers.Serializer):
    """Serializer for login request."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def to_login_request(self) -> LoginRequest:
        """Convert validated data to LoginRequest DTO.

        Returns:
            LoginRequest DTO
        """
        return LoginRequest(
            email=self.validated_data['email'],
            password=self.validated_data['password'],
        )


class RegisterSerializer(serializers.Serializer):
    """Serializer for registration request."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(min_length=1, max_length=255)

    def validate_email(self, value: str) -> str:
        """Validate email format.

        Args:
            value: Email address

        Returns:
            Validated email

        Raises:
            ValidationError: If email format is invalid
        """
        from apps.accounts.domain.invariants import (
            UserInvariantViolationError,
            validate_email_format,
        )

        try:
            validate_email_format(value)
        except UserInvariantViolationError as e:
            raise serializers.ValidationError(str(e))

        return value

    def to_register_request(self) -> RegisterRequest:
        """Convert validated data to RegisterRequest DTO.

        Returns:
            RegisterRequest DTO
        """
        return RegisterRequest(
            email=self.validated_data['email'],
            password=self.validated_data['password'],
            display_name=self.validated_data['display_name'],
        )


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response."""

    user = UserSerializer()
    token = serializers.CharField()


class RegisterResponseSerializer(serializers.Serializer):
    """Serializer for registration response."""

    user = UserSerializer()
    token = serializers.CharField()


class UpdateProfileSerializer(serializers.Serializer):
    """Serializer for profile update request."""

    display_name = serializers.CharField(required=False, allow_null=True)
    default_workspace_id = serializers.UUIDField(required=False, allow_null=True)

    def to_update_request(self) -> UpdateProfileRequest:
        """Convert validated data to UpdateProfileRequest DTO.

        Returns:
            UpdateProfileRequest DTO
        """
        return UpdateProfileRequest(
            display_name=self.validated_data.get('display_name'),
            default_workspace_id=self.validated_data.get('default_workspace_id'),
        )
