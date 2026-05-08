"""User-friendly error response formatting."""
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from shared.domain.exceptions import (
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    StateTransitionError,
    ValidationError,
)


def _error_payload(exc: Exception, context: dict[str, Any]) -> dict[str, Any]:
    """Custom exception handler for user-friendly error responses.

    Maps domain exceptions to appropriate HTTP responses with clear messages.
    """
    # Handle domain exceptions
    if isinstance(exc, NotFoundError):
        return {
            'error': 'not_found',
            'message': exc.message,
            'details': exc.details,
            'status': status.HTTP_404_NOT_FOUND,
        }

    if isinstance(exc, PermissionDeniedError):
        return {
            'error': 'permission_denied',
            'message': exc.message,
            'details': exc.details,
            'status': status.HTTP_403_FORBIDDEN,
        }

    if isinstance(exc, ValidationError):
        return {
            'error': 'validation_error',
            'message': exc.message,
            'details': exc.details,
            'status': status.HTTP_400_BAD_REQUEST,
        }

    if isinstance(exc, DomainError):
        return {
            'error': 'domain_error',
            'message': exc.message,
            'details': exc.details,
            'status': status.HTTP_400_BAD_REQUEST,
        }

    if isinstance(exc, StateTransitionError):
        return {
            'error': 'state_transition_error',
            'message': str(exc),
            'details': {
                'current_state': exc.current_state,
                'target_state': exc.target_state,
            },
            'status': status.HTTP_409_CONFLICT,
        }

    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        return {
            'error': 'validation_error',
            'message': 'Validation failed',
            'details': {'errors': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)},
            'status': status.HTTP_400_BAD_REQUEST,
        }

    # Default to REST framework's handler
    response = exception_handler(exc, context)

    if response is not None:
        # Customize standard DRF error responses
        data = response.data

        # Convert to user-friendly format
        if isinstance(data, dict):
            return {
                'error': 'request_error',
                'message': 'Invalid request',
                'details': data,
                'status': response.status_code,
            }

    return {
        'error': 'internal_error',
        'message': 'An internal error occurred',
        'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
    }


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """Return a DRF Response for framework-level exception handling."""
    result = _error_payload(exc, context)
    http_status = result.pop('status', status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(result, status=http_status)


def error_handler(exc: Exception) -> Response:
    """Convert exception to DRF Response for use in API views."""
    result = _error_payload(exc, context={})
    http_status = result.pop('status', status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(result, status=http_status)
