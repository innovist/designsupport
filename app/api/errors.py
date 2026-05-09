"""
Standardised error response helpers.
"""

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.infrastructure.ai_clients.factory import SettingsRequiredError


def settings_required_response(exc: SettingsRequiredError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "settings_required",
            "message": str(exc),
            "details": {"feature_key": exc.feature_key},
            "retry_possible": False,
            "action_required": "settings",
        },
    )


def not_found_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": message,
            "retry_possible": False,
            "action_required": "none",
        },
    )


def validation_error_response(message: str) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": message,
            "retry_possible": True,
            "action_required": "none",
        },
    )


def copyright_blocked_response(reference_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": "copyright_blocked",
            "message": f"Reference {reference_id} is blocked due to high copyright risk.",
            "details": {"reference_id": reference_id},
            "retry_possible": False,
            "action_required": "none",
        },
    )


def generation_failed_response(reason: str) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "generation_failed",
            "message": reason,
            "retry_possible": True,
            "action_required": "retry",
        },
    )
