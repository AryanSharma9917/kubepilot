"""Audit API routes."""

from fastapi import APIRouter, Query

from kubepilot_api.audit import recent_audit_events
from kubepilot_api.schemas import AuditEventResponse, AuditEventsResponse

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/events", response_model=AuditEventsResponse)
async def audit_events(
    limit: int = Query(default=50, ge=1, le=200),
) -> AuditEventsResponse:
    """Return recent local audit events."""

    return AuditEventsResponse(
        events=[
            AuditEventResponse(
                timestamp=event.timestamp,
                method=event.method,
                path=event.path,
                status_code=event.status_code,
            )
            for event in recent_audit_events(limit=limit)
        ]
    )
