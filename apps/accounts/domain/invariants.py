"""Account domain invariants.

Business rules that must always hold true for User entities.
"""
import re


class UserInvariantViolationError(Exception):
    """Raised when a user invariant is violated."""


def validate_email_format(email: str) -> None:
    """Validate email format."""
    if not email:
        raise UserInvariantViolationError("Email cannot be empty")

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise UserInvariantViolationError(f"Invalid email format: {email}")

    if ".." in email:
        raise UserInvariantViolationError(f"Email cannot contain consecutive dots: {email}")

    if len(email) > 255:
        raise UserInvariantViolationError("Email exceeds maximum length of 255 characters")


def validate_password_strength(password: str) -> None:
    """Validate password strength requirements."""
    if not password:
        raise UserInvariantViolationError("Password cannot be empty")
    if len(password) < 8:
        raise UserInvariantViolationError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise UserInvariantViolationError("Password cannot exceed 128 characters")
    if not any(c.isalpha() for c in password):
        raise UserInvariantViolationError("Password must contain at least one letter")
    if not any(c.isdigit() for c in password):
        raise UserInvariantViolationError("Password must contain at least one digit")


def validate_display_name(display_name: str) -> None:
    """Validate display name."""
    if not display_name or not display_name.strip():
        raise UserInvariantViolationError("Display name cannot be empty")
    if len(display_name.strip()) > 100:
        raise UserInvariantViolationError("Display name cannot exceed 100 characters")


def check_user_invariants(email: str, password: str, display_name: str) -> None:
    """Check all user invariants before creation."""
    validate_email_format(email)
    validate_password_strength(password)
    validate_display_name(display_name)
