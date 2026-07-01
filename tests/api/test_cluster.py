import httpx
import pytest


@pytest.mark.anyio
async def test_cluster_health_returns_unhealthy_workloads(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/cluster/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["unhealthy_count"] == 2
    assert [workload["name"] for workload in body["workloads"]] == [
        "checkout",
        "metrics-scraper",
    ]


@pytest.mark.anyio
async def test_cluster_health_filters_by_namespace(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/cluster/health", params={"namespace": "payments"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["unhealthy_count"] == 1
    assert body["workloads"][0]["namespace"] == "payments"
    assert body["workloads"][0]["name"] == "checkout"
