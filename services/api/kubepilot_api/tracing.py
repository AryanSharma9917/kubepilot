"""Lightweight tracing primitives for local development."""

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from time import perf_counter, time
from uuid import uuid4

from fastapi import Request, Response

MAX_TRACE_SPANS = 500
TRACE_SPANS: deque["TraceSpan"] = deque(maxlen=MAX_TRACE_SPANS)
CURRENT_TRACE_ID: ContextVar[str | None] = ContextVar("kubepilot_trace_id", default=None)


@dataclass(frozen=True)
class TraceSpan:
    """One local trace span."""

    trace_id: str
    name: str
    started_at: float
    duration_ms: float
    attributes: dict[str, str] = field(default_factory=dict)


async def trace_middleware(request: Request, call_next: object) -> Response:
    """Create a trace around each HTTP request."""

    trace_id = request.headers.get("x-trace-id") or str(uuid4())
    token = CURRENT_TRACE_ID.set(trace_id)
    try:
        with trace_span(
            "http.request",
            method=request.method,
            path=request.url.path,
        ):
            response = await call_next(request)
        response.headers["x-trace-id"] = trace_id
        return response
    finally:
        CURRENT_TRACE_ID.reset(token)


@contextmanager
def trace_span(name: str, **attributes: str):
    """Record a local span using the current trace id."""

    trace_id = CURRENT_TRACE_ID.get() or str(uuid4())
    started = perf_counter()
    started_at = time()
    try:
        yield
    finally:
        TRACE_SPANS.append(
            TraceSpan(
                trace_id=trace_id,
                name=name,
                started_at=started_at,
                duration_ms=(perf_counter() - started) * 1000,
                attributes=attributes,
            )
        )


def recent_trace_spans(*, limit: int = 50) -> list[TraceSpan]:
    """Return recent spans first."""

    return list(reversed(TRACE_SPANS))[:limit]
