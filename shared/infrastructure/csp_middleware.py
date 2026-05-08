"""Content-Security-Policy middleware.

Reads CONTENT_SECURITY_POLICY from Django settings and injects the
CSP header into every HTTP response. No third-party dependency required.
"""
from django.conf import settings
from django.http import HttpRequest, HttpResponse


def _build_csp_header(policy: dict[str, list[str]]) -> str:
    """Convert a policy dict to a CSP header value string."""
    directives: list[str] = []
    for directive, sources in policy.items():
        directives.append(f"{directive} {' '.join(sources)}")
    return "; ".join(directives)


class CSPMiddleware:
    """Add Content-Security-Policy header to responses."""

    def __init__(self, get_response):
        self.get_response = get_response
        policy = getattr(settings, "CONTENT_SECURITY_POLICY", None)
        self._header_value = _build_csp_header(policy) if policy else ""

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if self._header_value:
            response["Content-Security-Policy"] = self._header_value
        return response
