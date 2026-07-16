import httpx
import pytest


@pytest.mark.anyio
async def test_service_info(client: httpx.AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "KubePilot API",
        "version": "0.1.0",
        "environment": "development",
    }


@pytest.mark.anyio
async def test_health_endpoint(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_readiness_endpoint(client: httpx.AsyncClient) -> None:
    response = await client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.anyio
async def test_metrics_endpoint_exposes_request_metrics(client: httpx.AsyncClient) -> None:
    await client.get("/healthz")
    await client.post("/api/v1/chat", json={"message": "Why is my deployment failing?"})
    await client.post(
        "/api/v1/knowledge/search",
        json={"query": "deployment rollout failures", "limit": 2},
    )
    await client.get("/api/v1/cluster/health")

    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "kubepilot_http_requests_total" in response.text
    assert 'path="/healthz"' in response.text
    assert "kubepilot_chat_responses_total" in response.text
    assert "kubepilot_chat_sources_total" in response.text
    assert "kubepilot_chat_citations_total" in response.text
    assert "kubepilot_knowledge_searches_total" in response.text
    assert "kubepilot_knowledge_results_total" in response.text
    assert "kubepilot_cluster_tool_calls_total" in response.text
    assert 'operation="cluster_health",result="degraded"' in response.text
    assert "kubepilot_cluster_tool_duration_seconds_total" in response.text
    assert "kubepilot_trace_spans_buffered" in response.text
