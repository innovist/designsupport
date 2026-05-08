"""Account domain services.

Password hashing using PBKDF2-HMAC-SHA256 (stdlib, no external deps).

The domain layer cannot depend on external packages. Infrastructure
layer adapters (e.g. using argon2-cffi) will override this for production.
"""
import hashlib
import secrets
from base64 import b64encode


# @MX:ANCHOR: [AUTO] Password hashing service used by authentication use cases
# @MX:REASON: High fan_in - called by RegisterUserUseCase and AuthenticateUseCase
class PasswordHasher:
    """Password hashing service using PBKDF2-HMAC-SHA256.

    OWASP-recommended parameters. Infrastructure layer may substitute
    argon2-cffi via the application port.
    """

    # @MX:NOTE: [AUTO] OWASP 2024 recommendation for PBKDF2-HMAC-SHA256
    _ITERATIONS = 600_000
    _SALT_LENGTH = 16
    _HASH_LENGTH = 32

    @classmethod
    # @MX:ANCHOR: [AUTO] Password hashing entry point for user registration
    # @MX:REASON: High fan_in - called by RegisterUserUseCase across multiple flows
    def hash(cls, password: str) -> str:
        """Hash a password.

        Returns:
            Format: ``pbkdf2_sha256$<iterations>$<base64-salt>$<base64-hash>``
        """
        if not password:
            raise ValueError("Password cannot be empty")

        salt = secrets.token_bytes(cls._SALT_LENGTH)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls._ITERATIONS,
            cls._HASH_LENGTH,
        )
        return (
            f"pbkdf2_sha256${cls._ITERATIONS}"
            f"${b64encode(salt).decode('ascii')}"
            f"${b64encode(dk).decode('ascii')}"
        )

    @classmethod
    # @MX:ANCHOR: [AUTO] Password verification for authentication
    # @MX:REASON: High fan_in - called by AuthenticateUseCase, critical security function
    def verify(cls, password: str, encoded: str) -> bool:
        """Verify a password against a stored hash.

        Args:
            password: Plain text password
            encoded: Stored hash string from :meth:`hash`

        Returns:
            True if password matches
        """
        if not password or not encoded:
            return False

        try:
            parts = encoded.split("$")
            if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
                return False

            iterations = int(parts[1])
            salt = __import__("base64").b64decode(parts[2])
            stored_hash = __import__("base64").b64decode(parts[3])

            computed = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                iterations,
                cls._HASH_LENGTH,
            )
            return secrets.compare_digest(stored_hash, computed)
        except (ValueError, IndexError):
            return False
