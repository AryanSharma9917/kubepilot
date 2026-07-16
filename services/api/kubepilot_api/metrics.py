"""Minimal Prometheus-style metrics for the API service."""

from collections import Counter
from time import perf_counter

from fastapi import Request, Response

REQUESTS: Counter[tuple[str, str, int]] = Counter()
REQUEST_SECONDS: Counter[tuple[str, str]] = Counter()
CHAT_RESPONSES: Counter[str] = Counter()
CHAT_SOURCES: Counter[str] = Counter()
CHAT_CITATIONS: Counter[str] = Counter()
KNOWLEDGE_SEARCHES: Counter[str] = Counter()
KNOWLEDGE_RESULTS: Counter[str] = Counter()
CLUSTER_TOOL_CALLS: Counter[tuple[str, str]] = Counter()
CLUSTER_TOOL_SECONDS: Counter[str] = Counter()


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
    lines.extend(
        [
            "# HELP kubepilot_chat_responses_total Total chat responses.",
            "# TYPE kubepilot_chat_responses_total counter",
            f"kubepilot_chat_responses_total {CHAT_RESPONSES['total']}",
            "# HELP kubepilot_chat_sources_total Total cited source titles in chat responses.",
            "# TYPE kubepilot_chat_sources_total counter",
            f"kubepilot_chat_sources_total {CHAT_SOURCES['total']}",
            "# HELP kubepilot_chat_citations_total Total structured citations in chat responses.",
            "# TYPE kubepilot_chat_citations_total counter",
            f"kubepilot_chat_citations_total {CHAT_CITATIONS['total']}",
        ]
    )
    lines.extend(
        [
            "# HELP kubepilot_knowledge_searches_total Total knowledge searches.",
            "# TYPE kubepilot_knowledge_searches_total counter",
            f"kubepilot_knowledge_searches_total {KNOWLEDGE_SEARCHES['total']}",
            "# HELP kubepilot_knowledge_results_total Total retrieved knowledge results.",
            "# TYPE kubepilot_knowledge_results_total counter",
            f"kubepilot_knowledge_results_total {KNOWLEDGE_RESULTS['total']}",
            "# HELP kubepilot_cluster_tool_calls_total Total Kubernetes tool calls.",
            "# TYPE kubepilot_cluster_tool_calls_total counter",
        ]
    )
    for (operation, result), count in sorted(CLUSTER_TOOL_CALLS.items()):
        lines.append(
            'kubepilot_cluster_tool_calls_total{'
            f'operation="{operation}",result="{result}"'
            f"}} {count}"
        )
    lines.extend(
        [
            "# HELP kubepilot_cluster_tool_duration_seconds_total "
            "Total Kubernetes tool execution time.",
            "# TYPE kubepilot_cluster_tool_duration_seconds_total counter",
        ]
    )
    for operation, total_seconds in sorted(CLUSTER_TOOL_SECONDS.items()):
        lines.append(
            'kubepilot_cluster_tool_duration_seconds_total{'
            f'operation="{operation}"'
            f"}} {total_seconds:.6f}"
        )
    lines.extend(
        [
            "# HELP kubepilot_trace_spans_buffered Current in-memory trace span count.",
            "# TYPE kubepilot_trace_spans_buffered gauge",
            f"kubepilot_trace_spans_buffered {_trace_span_count()}",
        ]
    )
    return "\n".join(lines) + "\n"


def record_chat_response(*, source_count: int, citation_count: int) -> None:
    """Record chat response-level metrics."""

    CHAT_RESPONSES["total"] += 1
    CHAT_SOURCES["total"] += source_count
    CHAT_CITATIONS["total"] += citation_count


def record_knowledge_search(*, result_count: int) -> None:
    """Record retrieval-level metrics."""

    KNOWLEDGE_SEARCHES["total"] += 1
    KNOWLEDGE_RESULTS["total"] += result_count


def record_cluster_tool_call(
    *,
    operation: str,
    result: str,
    elapsed_seconds: float,
) -> None:
    """Record Kubernetes tool call metrics."""

    CLUSTER_TOOL_CALLS[(operation, result)] += 1
    CLUSTER_TOOL_SECONDS[operation] += elapsed_seconds


def _trace_span_count() -> int:
    from kubepilot_api.tracing import TRACE_SPANS

    return len(TRACE_SPANS)
