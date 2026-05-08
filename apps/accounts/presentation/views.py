"""API views for accounts module.

Defines views for authentication and profile management.
"""
from typing import Any

from django.http import HttpRequest
from asgiref.sync import async_to_sync
from django.contrib.auth import login as django_login
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from shared.presentation.base_views import BaseAPIView
from shared.presentation.error_handlers import error_handler


def _attach_login_session(request: HttpRequest, user_id) -> None:
    """Persist Django session tenant context after successful auth."""
    from apps.accounts.infrastructure.orm.models import UserModel
    from apps.workspaces.infrastructure.orm.models import Workspace

    user = UserModel.objects.get(id=user_id)
    django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    if user.default_workspace_id:
        workspace = Workspace.all_objects.get(id=user.default_workspace_id)
        request.session["tenant_id"] = workspace.tenant_id
        request.session["workspace_id"] = str(workspace.id)


# @MX:ANCHOR: [AUTO] User registration endpoint - entry point for new accounts
# @MX:REASON: High fan_in - called by frontend, mobile apps, API clients
class RegisterView(APIView):
    """View for user registration."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: HttpRequest) -> Response:
        """Register a new user.

        Args:
            request: HTTP request with registration data

        Returns:
            Response with user data and authentication token
        """
        from apps.accounts.application.container import AccountsContainer
        from apps.accounts.presentation.serializers import (
            RegisterSerializer,
            RegisterResponseSerializer,
        )

        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=400,
            )

        try:
            # Get use case from container (dependency injection)
            container = AccountsContainer()
            use_case = container.register_user()

            # Execute use case
            register_request = serializer.to_register_request()
            result = async_to_sync(use_case.execute)(register_request)

            if result.is_failure:
                return error_handler(result.error)

            response_data = result.value
            _attach_login_session(request, response_data.user.id)

            # Serialize response
            response_serializer = RegisterResponseSerializer(response_data)

            return Response(response_serializer.data, status=201)

        except Exception as e:
            return error_handler(e)


# @MX:ANCHOR: [AUTO] Authentication endpoint - JWT token issuance
# @MX:REASON: High fan_in - called by all clients requiring authenticated access
class LoginView(APIView):
    """View for user authentication."""

    permission_classes = [permissions.AllowAny]

    def post(self, request: HttpRequest) -> Response:
        """Authenticate user with email and password.

        Args:
            request: HTTP request with login credentials

        Returns:
            Response with user data and authentication token
        """
        from apps.accounts.application.container import AccountsContainer
        from apps.accounts.presentation.serializers import (
            LoginSerializer,
            LoginResponseSerializer,
        )

        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=400,
            )

        try:
            # Get use case from container (dependency injection)
            container = AccountsContainer()
            use_case = container.authenticate()

            # Execute use case
            login_request = serializer.to_login_request()
            result = async_to_sync(use_case.execute)(login_request)

            if result.is_failure:
                return error_handler(result.error)

            response_data = result.value
            _attach_login_session(request, response_data.user.id)

            # Serialize response
            response_serializer = LoginResponseSerializer(response_data)

            return Response(response_serializer.data, status=200)

        except Exception as e:
            return error_handler(e)


class ProfileView(BaseAPIView):
    """View for user profile management."""

    def get(self, request: HttpRequest) -> Response:
        """Get current user profile.

        Args:
            request: HTTP request

        Returns:
            Response with user profile data
        """
        from apps.accounts.presentation.serializers import UserSerializer

        user_id = getattr(request, 'current_user_id', None)

        if not user_id:
            from rest_framework.exceptions import AuthenticationFailed

            return error_handler(AuthenticationFailed('User not authenticated'))

        try:
            from apps.accounts.application.container import AccountsContainer
            from apps.accounts.presentation.serializers import UserSerializer

            # Get use case from container
            container = AccountsContainer()
            use_case = container.get_profile()

            # Execute use case
            result = async_to_sync(use_case.execute)(user_id)

            if result.is_failure:
                return error_handler(result.error)

            user_dto = result.value
            serializer = UserSerializer(user_dto)

            return Response(serializer.data, status=200)

        except Exception as e:
            return error_handler(e)

    def patch(self, request: HttpRequest) -> Response:
        """Update user profile.

        Args:
            request: HTTP request with profile update data

        Returns:
            Response with updated user profile
        """
        from apps.accounts.presentation.serializers import (
            UpdateProfileSerializer,
            UserSerializer,
        )

        user_id = getattr(request, 'current_user_id', None)

        if not user_id:
            from rest_framework.exceptions import AuthenticationFailed

            return error_handler(AuthenticationFailed('User not authenticated'))

        serializer = UpdateProfileSerializer(data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=400,
            )

        try:
            from apps.accounts.application.container import AccountsContainer
            from apps.accounts.presentation.serializers import UserSerializer

            # Get use case from container
            container = AccountsContainer()
            use_case = container.update_profile()

            # Execute use case
            update_request = serializer.to_update_request()
            result = async_to_sync(use_case.execute)(user_id, update_request)

            if result.is_failure:
                return error_handler(result.error)

            user_dto = result.value
            response_serializer = UserSerializer(user_dto)

            return Response(response_serializer.data, status=200)

        except Exception as e:
            return error_handler(e)


class LogoutView(BaseAPIView):
    """View for user logout."""

    def post(self, request: HttpRequest) -> Response:
        """Logout current user.

        Args:
            request: HTTP request

        Returns:
            Response confirming logout
        """
        # TODO: Implement token invalidation if using refresh tokens
        # For now, just return success (client should discard token)
        return Response(
            {'message': 'Successfully logged out'},
            status=200,
        )
