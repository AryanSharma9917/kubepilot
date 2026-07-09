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

    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "kubepilot_http_requests_total" in response.text
    assert 'path="/healthz"' in response.text
    assert "kubepilot_chat_responses_total" in response.text
    assert "kubepilot_chat_sources_total" in response.text
    assert "kubepilot_chat_citations_total" in response.text
