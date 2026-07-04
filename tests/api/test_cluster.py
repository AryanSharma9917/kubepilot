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


@pytest.mark.anyio
async def test_deployment_diagnosis_returns_pods_events_and_recommendations(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose")

    assert response.status_code == 200
    body = response.json()
    assert body["namespace"] == "payments"
    assert body["name"] == "checkout"
    assert body["health"]["status"] == "Degraded"
    assert [pod["reason"] for pod in body["pods"]] == ["CrashLoopBackOff", "ImagePullBackOff"]
    assert body["events"][0]["event_type"] == "Warning"
    assert body["logs"][0]["previous"] is True
    assert "PAYMENT_GATEWAY_URL" in body["logs"][0]["text"]
    assert body["recommendations"]


@pytest.mark.anyio
async def test_deployment_diagnosis_returns_404_for_missing_deployment(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/cluster/namespaces/default/deployments/missing/diagnose")

    assert response.status_code == 404
