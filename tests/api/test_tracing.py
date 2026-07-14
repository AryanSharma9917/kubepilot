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
