import httpx
import pytest
from kubepilot_api.tracing import TRACE_SPANS


@pytest.mark.anyio
async def test_trace_middleware_records_http_request_span(client: httpx.AsyncClient) -> None:
    TRACE_SPANS.clear()

    response = await client.get("/healthz", headers={"x-trace-id": "trace-1"})
    traces_response = await client.get("/api/v1/traces", params={"limit": 10})

    assert response.headers["x-trace-id"] == "trace-1"
    assert traces_response.status_code == 200
    body = traces_response.json()
    assert any(
        span["trace_id"] == "trace-1" and span["name"] == "http.request"
        for span in body["spans"]
    )


@pytest.mark.anyio
async def test_trace_spans_include_agent_and_retrieval_work(
    client: httpx.AsyncClient,
) -> None:
    TRACE_SPANS.clear()

    chat_response = await client.post(
        "/api/v1/chat",
        json={"message": "why is checkout unhealthy"},
        headers={"x-trace-id": "trace-work"},
    )
    search_response = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "image pull failures", "limit": 2},
        headers={"x-trace-id": "trace-work"},
    )
    traces_response = await client.get("/api/v1/traces", params={"limit": 20})

    assert chat_response.status_code == 200
    assert search_response.status_code == 200
    body = traces_response.json()
    spans = [
        span
        for span in body["spans"]
        if span["trace_id"] == "trace-work"
    ]
    assert {span["name"] for span in spans} >= {"agent.respond", "knowledge.search"}
    assert any(
        span["name"] == "knowledge.search" and span["attributes"]["limit"] == "2"
        for span in spans
    )
