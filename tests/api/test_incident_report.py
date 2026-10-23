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
    assert body["report_id"]
    assert body["generated_at"]
    assert body["title"] == "Deployment incident: payments/deployment/checkout"
    assert body["severity"] in {"warning", "critical"}
    assert body["impacted_resource"] == "payments/deployment/checkout"
    assert body["probable_cause"]
    assert body["operator_impact"]
    assert body["status_update"]
    assert body["evidence"]
    assert body["timeline"]
    assert body["timeline"][0]["source"] == "deployment"
    assert body["next_actions"]


@pytest.mark.anyio
async def test_generated_incident_reports_can_be_listed_and_fetched(
    client: httpx.AsyncClient,
) -> None:
    generated_response = await client.get(
        "/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report"
    )
    report_id = generated_response.json()["report_id"]

    list_response = await client.get("/api/v1/cluster/incident-reports")
    detail_response = await client.get(f"/api/v1/cluster/incident-reports/{report_id}")

    assert list_response.status_code == 200
    summaries = list_response.json()["reports"]
    assert summaries
    assert summaries[0]["report_id"] == report_id
    assert summaries[0]["impacted_resource"] == "payments/deployment/checkout"
    assert detail_response.status_code == 200
    assert detail_response.json()["report_id"] == report_id


@pytest.mark.anyio
async def test_generated_incident_report_returns_404_for_unknown_id(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/cluster/incident-reports/missing")

    assert response.status_code == 404


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
    assert "## Probable Cause" in response.text
    assert "## Operator Impact" in response.text
    assert "## Status Update" in response.text
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
