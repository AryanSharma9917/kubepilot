"""Minimal Prometheus-style metrics for the API service."""

from collections import Counter
from time import perf_counter

from fastapi import Request, Response

REQUESTS: Counter[tuple[str, str, int]] = Counter()
REQUEST_SECONDS: Counter[tuple[str, str]] = Counter()


async def metrics_middleware(request: Request, call_next: object) -> Response:
    """Record basic request count and latency metrics."""

    started = perf_counter()
    response = await call_next(request)
    elapsed = perf_counter() - started
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    method = request.method
    REQUESTS[(method, path, response.status_code)] += 1
    REQUEST_SECONDS[(method, path)] += elapsed
    return response


def render_metrics() -> str:
    """Render metrics in the Prometheus text exposition format."""

    lines = [
        "# HELP kubepilot_http_requests_total Total HTTP requests.",
        "# TYPE kubepilot_http_requests_total counter",
    ]
    for (method, path, status_code), count in sorted(REQUESTS.items()):
        lines.append(
            'kubepilot_http_requests_total{'
            f'method="{method}",path="{path}",status_code="{status_code}"'
            f"}} {count}"
        )

    lines.extend(
        [
            "# HELP kubepilot_http_request_duration_seconds_total Total HTTP request time.",
            "# TYPE kubepilot_http_request_duration_seconds_total counter",
        ]
    )
    for (method, path), total_seconds in sorted(REQUEST_SECONDS.items()):
        lines.append(
            'kubepilot_http_request_duration_seconds_total{'
            f'method="{method}",path="{path}"'
            f"}} {total_seconds:.6f}"
        )
    return "\n".join(lines) + "\n"
