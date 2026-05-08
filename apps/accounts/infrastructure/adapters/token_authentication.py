"""Authentication adapter for DesignSupport signed bearer tokens."""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from base64 import urlsafe_b64decode

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.infrastructure.orm.models import UserModel


class SignedTokenAuthentication(BaseAuthentication):
    """Authenticate the HMAC token issued by DjangoAuthService."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None

        if header[0].decode().lower() not in {"bearer", "token"}:
            return None
        if len(header) != 2:
            raise AuthenticationFailed("Invalid authorization header")

        token = header[1].decode()
        payload = self._decode_token(token)
        try:
            user = UserModel.objects.get(id=payload["sub"], is_active=True)
        except UserModel.DoesNotExist as exc:
            raise AuthenticationFailed("User not found") from exc
        return (user, payload)

    def _decode_token(self, token):
        try:
            payload_b64, signature = token.split(".", 1)
        except ValueError as exc:
            raise AuthenticationFailed("Invalid token format") from exc

        expected = hmac.new(
            settings.SECRET_KEY.encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise AuthenticationFailed("Invalid token signature")

        try:
            payload = json.loads(urlsafe_b64decode(payload_b64.encode()).decode())
        except (ValueError, json.JSONDecodeError) as exc:
            raise AuthenticationFailed("Invalid token payload") from exc
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            raise AuthenticationFailed("Token expired")
        return payload
