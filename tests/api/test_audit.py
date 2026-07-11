import httpx
import pytest
from kubepilot_api.audit import AUDIT_EVENTS


@pytest.mark.anyio
async def test_audit_events_records_api_requests(client: httpx.AsyncClient) -> None:
    AUDIT_EVENTS.clear()

    health_response = await client.get("/healthz", headers={"x-request-id": "test-request"})
    response = await client.get("/api/v1/audit/events", params={"limit": 5})

    assert health_response.headers["x-request-id"] == "test-request"
    assert response.status_code == 200
    body = response.json()
    paths = [event["path"] for event in body["events"]]
    assert "/healthz" in paths
    health_event = next(event for event in body["events"] if event["path"] == "/healthz")
    assert health_event["request_id"] == "test-request"
