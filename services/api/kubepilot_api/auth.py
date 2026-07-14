"""Optional API key authentication middleware."""

from fastapi import Request, Response
from starlette.responses import JSONResponse

from kubepilot_api.config import get_settings

PUBLIC_PATHS = {"/", "/healthz", "/readyz", "/metrics"}


async def api_key_auth_middleware(request: Request, call_next: object) -> Response:
    """Require an API key for API routes when keys are configured."""

    settings = get_settings()
    if not settings.api_keys or request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    if not request.url.path.startswith("/api/"):
        return await call_next(request)

    candidate = _api_key_from_request(request)
    if candidate in settings.api_keys:
        return await call_next(request)

    return JSONResponse(
        status_code=401,
        content={"detail": "Missing or invalid API key"},
    )


def _api_key_from_request(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return request.headers.get("x-api-key")
