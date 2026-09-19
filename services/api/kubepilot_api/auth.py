"""API key and optional OIDC authentication middleware."""

from functools import lru_cache
from typing import Any

import jwt
from fastapi import Request, Response
from starlette.responses import JSONResponse

from kubepilot_api.config import get_settings

PUBLIC_PATHS = {"/", "/healthz", "/readyz", "/metrics"}


async def api_key_auth_middleware(request: Request, call_next: object) -> Response:
    """Authenticate API requests with an API key or configured OIDC token."""

    settings = get_settings()
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    if not settings.api_keys and not settings.oidc_issuer:
        return await call_next(request)

    candidate = _api_key_from_request(request)
    if candidate in settings.api_keys and not settings.oidc_required:
        return await call_next(request)

    token = _bearer_token(request)
    if token and settings.oidc_issuer:
        try:
            claims = _decode_oidc_token(token, settings)
        except (OSError, ValueError, jwt.PyJWTError):
            return _unauthorized()
        if not _has_action_access(claims, request.url.path, settings):
            return JSONResponse(status_code=403, content={"detail": "OIDC role is not allowed"})
        request.state.oidc_claims = claims
        return await call_next(request)

    return _unauthorized()


def _api_key_from_request(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return request.headers.get("x-api-key")


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


@lru_cache(maxsize=8)
def _jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url)


def _decode_oidc_token(token: str, settings: Any) -> dict[str, Any]:
    if not settings.oidc_audience or not settings.oidc_jwks_url:
        raise ValueError("OIDC audience and JWKS URL are required")
    signing_key = _jwks_client(settings.oidc_jwks_url).get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
        audience=settings.oidc_audience,
        issuer=settings.oidc_issuer,
        options={"require": ["exp", "iss", "sub"]},
    )
    return claims


def _has_action_access(claims: dict[str, Any], path: str, settings: Any) -> bool:
    roles = claims.get(settings.oidc_role_claim, ())
    if isinstance(roles, str):
        roles = roles.split()
    if not isinstance(roles, (list, tuple, set)):
        return False
    action = _action_for_path(path)
    role_actions = dict(settings.oidc_role_actions)
    return any(
        action in role_actions.get(role, ()) or "*" in role_actions.get(role, ())
        for role in roles
    )


def _action_for_path(path: str) -> str:
    if path.startswith("/api/v1/chat"):
        return "chat"
    if path.startswith("/api/v1/knowledge/"):
        return "knowledge:search"
    if path.endswith("/health"):
        return "cluster:health"
    if path.endswith("/diagnose"):
        return "deployment:diagnose"
    if path.endswith("/incident-report") or path.endswith("/incident-report.md"):
        return "deployment:incident-report"
    if path.endswith("/remediation-plan"):
        return "deployment:remediation-plan"
    return "system:read"


def _unauthorized() -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "Missing or invalid credentials"})
