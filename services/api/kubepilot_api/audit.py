"""Bounded audit trail for local development and single-process deployments."""

from collections import deque
from dataclasses import dataclass
from time import time
from uuid import uuid4

from fastapi import Request, Response

from kubepilot_api.config import get_settings

MAX_AUDIT_EVENTS = 200
AUDIT_EVENTS: deque["AuditEvent"] = deque()


@dataclass(frozen=True)
class AuditEvent:
    """One API request audit event."""

    timestamp: float
    request_id: str
    method: str
    path: str
    status_code: int


async def audit_middleware(request: Request, call_next: object) -> Response:
    """Record an audit event for each API request."""

    request_id = request.headers.get("x-request-id") or str(uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    AUDIT_EVENTS.append(
        AuditEvent(
            timestamp=time(),
            request_id=request_id,
            method=request.method,
            path=path,
            status_code=response.status_code,
        )
    )
    retention = max(1, get_settings().audit_retention_events)
    while len(AUDIT_EVENTS) > retention:
        AUDIT_EVENTS.popleft()
    return response


def recent_audit_events(*, limit: int = 50) -> list[AuditEvent]:
    """Return the most recent audit events first."""

    return list(reversed(AUDIT_EVENTS))[:limit]
