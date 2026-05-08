"""SSRF protection with URL allowlist validation."""
from urllib.parse import urlparse

from shared.domain.exceptions import ValidationError


class SSRFGuard:
    """SSRF protection using URL allowlist."""

    # Default allowlist (internal services)
    DEFAULT_ALLOWLIST = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
    ]

    # Blocked private IP ranges (RFC 1918)
    BLOCKED_RANGES = [
        '10.0.0.0/8',
        '172.16.0.0/12',
        '192.168.0.0/16',
    ]

    def __init__(self, allowlist: list[str] | None = None) -> None:
        """Initialize guard with custom allowlist."""
        self.allowlist = set(allowlist or self.DEFAULT_ALLOWLIST)

    def validate_url(self, url: str) -> str:
        """Validate URL against allowlist.

        Returns:
            Normalized URL if valid

        Raises:
            ValidationError: If URL is blocked or invalid
        """
        try:
            parsed = urlparse(url)

            # Check for missing scheme
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError('url', 'URL must have scheme and netloc')

            # Block internal IPs unless in allowlist
            hostname = parsed.hostname

            if hostname in self.allowlist:
                return url

            # Block private IP ranges
            if self._is_private_ip(hostname):
                raise ValidationError(
                    'url',
                    f'URL hostname {hostname} is in private IP range'
                )

            # Block metadata endpoints (cloud services)
            if hostname in ['169.254.169.254', 'metadata.google.internal']:
                raise ValidationError(
                    'url',
                    f'URL hostname {hostname} is a metadata endpoint'
                )

            return url

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError('url', f'Invalid URL: {e}')

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname is a private IP."""
        import ipaddress

        try:
            ip = ipaddress.ip_address(hostname)
            return any(ip.network in [ipaddress.network(n) for n in self.BLOCKED_RANGES])
        except ValueError:
            return False


SSRF_GUARD = SSRFGuard()
