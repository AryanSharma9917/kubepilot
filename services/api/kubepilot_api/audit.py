"""In-memory audit trail for local development."""

from collections import deque
from dataclasses import dataclass
from time import time

from fastapi import Request, Response

MAX_AUDIT_EVENTS = 200
AUDIT_EVENTS: deque["AuditEvent"] = deque(maxlen=MAX_AUDIT_EVENTS)


@dataclass(frozen=True)
class AuditEvent:
    """One API request audit event."""

    timestamp: float
    method: str
    path: str
    status_code: int


async def audit_middleware(request: Request, call_next: object) -> Response:
    """Record an audit event for each API request."""

    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    AUDIT_EVENTS.append(
        AuditEvent(
            timestamp=time(),
            method=request.method,
            path=path,
            status_code=response.status_code,
        )
    )
    return response


def recent_audit_events(*, limit: int = 50) -> list[AuditEvent]:
    """Return the most recent audit events first."""

    return list(reversed(AUDIT_EVENTS))[:limit]
