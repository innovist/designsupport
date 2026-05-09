"""
CORS and security middleware configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def configure_cors(app: FastAPI) -> None:
    """Attach permissive CORS middleware for single-user local deployment."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
