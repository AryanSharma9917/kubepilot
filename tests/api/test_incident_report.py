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
    assert body["timeline"]
    assert body["timeline"][0]["source"] == "deployment"
    assert body["next_actions"]


@pytest.mark.anyio
async def test_deployment_incident_report_markdown_export(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report.md"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "# Deployment incident: payments/deployment/checkout" in response.text
    assert "## Evidence" in response.text
    assert "## Next Actions" in response.text


@pytest.mark.anyio
async def test_deployment_incident_report_returns_404_for_unknown_deployment(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/cluster/namespaces/default/deployments/missing/incident-report"
    )

    assert response.status_code == 404
