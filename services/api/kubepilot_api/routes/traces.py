"""Trace API routes."""

from fastapi import APIRouter, Query

from kubepilot_api.schemas import TraceSpanResponse, TraceSpansResponse
from kubepilot_api.tracing import recent_trace_spans

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])


@router.get("", response_model=TraceSpansResponse)
async def trace_spans(
    limit: int = Query(default=50, ge=1, le=500),
) -> TraceSpansResponse:
    """Return recent local trace spans."""

    return TraceSpansResponse(
        spans=[
            TraceSpanResponse(
                trace_id=span.trace_id,
                name=span.name,
                started_at=span.started_at,
                duration_ms=span.duration_ms,
                attributes=span.attributes,
            )
            for span in recent_trace_spans(limit=limit)
        ]
    )
