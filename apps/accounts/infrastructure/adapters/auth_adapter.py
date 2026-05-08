"""Authentication service adapter implementation.

Implements AuthServicePort using domain PasswordHasher for password hashing
and JWT-compatible token generation.
"""
import hashlib
import hmac
import json
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from uuid import UUID

from django.conf import settings

from apps.accounts.domain.services import PasswordHasher
from shared.infrastructure.tenant_middleware.middleware import TenantContext


class DjangoAuthService:
    """Django-based implementation of AuthServicePort.

    Uses domain PasswordHasher (PBKDF2) for passwords and HMAC-SHA256
    for stateless tokens. JWT integration via djangorestframework-simplejwt
    should replace token logic in production.
    """

    def __init__(self):
        self._hasher = PasswordHasher()

    async def hash_password(self, password: str) -> str:
        """Hash password using PBKDF2-HMAC-SHA256."""
        return self._hasher.hash(password)

    async def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against stored hash."""
        return self._hasher.verify(password, password_hash)

    async def create_token(self, user_id: UUID) -> str:
        """Create HMAC-SHA256 signed token for user.

        Uses a simple two-part base64url token (header.payload) with HMAC
        signature. Replace with proper JWT library in production.
        """
        tenant_id, workspace_id, _ = TenantContext.get()

        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "tid": tenant_id,
            "wid": str(workspace_id) if workspace_id else None,
            "exp": int((now + timedelta(hours=24)).timestamp()),
            "iat": int(now.timestamp()),
        }

        payload_b64 = urlsafe_b64encode(json.dumps(payload).encode()).decode()
        signature = hmac.new(
            settings.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256
        ).hexdigest()

        return f"{payload_b64}.{signature}"
