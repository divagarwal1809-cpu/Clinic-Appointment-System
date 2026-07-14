"""
In-memory sliding-window rate limiter middleware for FastAPI/Starlette.

Rules (per client IP):
  - POST /appointments/book-with-intake   → 10 requests / 60 seconds
  - POST /intake-forms/*/summarize        → 5  requests / 60 seconds
  - All other routes                      → 60 requests / 60 seconds

Returns HTTP 429 with Retry-After header when the limit is exceeded.
No external dependencies required — uses only the stdlib `collections.deque`.
"""

import re
import time
import logging
from collections import defaultdict, deque
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Route-specific limits: (path_pattern, method, max_requests, window_seconds)
# Evaluated in order; first match wins.
# ---------------------------------------------------------------------------
_ROUTE_LIMITS = [
    (re.compile(r"^/appointments/book-with-intake$"), "POST", 10, 60),
    (re.compile(r"^/intake-forms/[^/]+/summarize$"), "POST", 5, 60),
]
_DEFAULT_LIMIT = (60, 60)  # (max_requests, window_seconds)


def _get_limit(path: str, method: str) -> tuple[int, int]:
    """Return (max_requests, window_seconds) for the given path+method."""
    for pattern, route_method, max_req, window in _ROUTE_LIMITS:
        if method.upper() == route_method and pattern.match(path):
            return max_req, window
    return _DEFAULT_LIMIT


def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP, respecting common reverse-proxy headers.
    Falls back to the direct connection address.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain a comma-separated list; take the leftmost
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter.

    State is stored in-memory as a dict of:
        (ip, path_key) → deque of request timestamps (floats, epoch seconds)

    The deque is pruned of entries older than the window on every request,
    so memory usage stays bounded even under sustained traffic.
    """

    def __init__(self, app):
        super().__init__(app)
        # {(ip, path_key): deque[float]}
        self._windows: dict[tuple[str, str], Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        ip = _get_client_ip(request)
        path = request.url.path
        method = request.method
        max_requests, window_seconds = _get_limit(path, method)

        # Build a bucket key: combine IP with the relevant route segment
        bucket = (ip, f"{method}:{path}")
        now = time.monotonic()
        window = self._windows[bucket]

        # Evict timestamps older than the sliding window
        cutoff = now - window_seconds
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= max_requests:
            retry_after = int(window_seconds - (now - window[0])) + 1
            logger.warning(
                "Rate limit exceeded | ip=%s path=%s method=%s limit=%d/%ds",
                ip, path, method, max_requests, window_seconds
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Too many requests. You have exceeded the limit of "
                        f"{max_requests} requests per {window_seconds} seconds "
                        f"for this endpoint. Please try again later."
                    )
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Window": str(window_seconds),
                },
            )

        # Record this request
        window.append(now)
        response = await call_next(request)
        # Expose remaining quota in response headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max_requests - len(window))
        response.headers["X-RateLimit-Window"] = str(window_seconds)
        return response
