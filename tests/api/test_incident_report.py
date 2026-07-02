import httpx
import pytest


@pytest.mark.anyio
async def test_deployment_incident_report_returns_structured_report(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Deployment incident: payments/deployment/checkout"
    assert body["severity"] in {"warning", "critical"}
    assert body["impacted_resource"] == "payments/deployment/checkout"
    assert body["evidence"]
    assert body["next_actions"]


@pytest.mark.anyio
async def test_deployment_incident_report_returns_404_for_unknown_deployment(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/cluster/namespaces/default/deployments/missing/incident-report"
    )

    assert response.status_code == 404
