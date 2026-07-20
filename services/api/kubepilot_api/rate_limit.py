"""Small in-memory request rate limiter."""

from collections import defaultdict, deque
from time import monotonic

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from kubepilot_api.config import get_settings

WINDOW_SECONDS = 60.0
RATE_LIMITED_PATH_PREFIXES = ("/api/",)
REQUEST_TIMESTAMPS: defaultdict[str, deque[float]] = defaultdict(deque)


async def rate_limit_middleware(request: Request, call_next: object) -> Response:
    """Apply an optional per-client request limit to API routes."""

    settings = get_settings()
    if settings.rate_limit_per_minute <= 0 or not request.url.path.startswith(
        RATE_LIMITED_PATH_PREFIXES
    ):
        return await call_next(request)

    now = monotonic()
    client_id = _client_id(request)
    timestamps = REQUEST_TIMESTAMPS[client_id]
    while timestamps and now - timestamps[0] >= WINDOW_SECONDS:
        timestamps.popleft()
    if len(timestamps) >= settings.rate_limit_per_minute:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(int(WINDOW_SECONDS))},
        )
    timestamps.append(now)
    return await call_next(request)


def _client_id(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is None:
        return "unknown"
    return request.client.host
