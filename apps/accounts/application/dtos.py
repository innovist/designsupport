"""Data Transfer Objects for accounts module.

Defines DTOs for use case inputs/outputs and API serialization.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class UserDTO:
    """User data transfer object."""

    id: UUID
    email: str
    display_name: str
    default_workspace_id: Optional[UUID]
    is_active: bool


@dataclass
class LoginRequest:
    """Login request DTO."""

    email: str
    password: str


@dataclass(frozen=True)
class LoginResponse:
    """Login response DTO."""

    user: UserDTO
    token: str


@dataclass
class RegisterRequest:
    """Registration request DTO."""

    email: str
    password: str
    display_name: str


@dataclass(frozen=True)
class RegisterResponse:
    """Registration response DTO."""

    user: UserDTO
    token: str


@dataclass
class UpdateProfileRequest:
    """Update profile request DTO."""

    display_name: Optional[str] = None
    default_workspace_id: Optional[UUID] = None
