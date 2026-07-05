import httpx
from kubepilot_api.local_cluster import validate_local_cluster_client


def _transport(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/healthz":
        return httpx.Response(200, json={"status": "ok"})
    if request.url.path == "/readyz":
        return httpx.Response(200, json={"status": "ready"})
    if request.url.path == "/metrics":
        return httpx.Response(
            200,
            text="# HELP kubepilot_http_requests_total Total HTTP requests.\n",
        )
    if request.url.path == "/api/v1/cluster/health":
        return httpx.Response(
            200,
            json={
                "status": "degraded",
                "unhealthy_count": 2,
                "workloads": [],
            },
        )
    return httpx.Response(404, json={"detail": "not found"})


def test_validate_local_cluster_client_accepts_expected_responses() -> None:
    transport = httpx.MockTransport(_transport)

    with httpx.Client(base_url="http://test", transport=transport) as client:
        result = validate_local_cluster_client(client, timeout_seconds=1, poll_interval_seconds=0)

    assert result.healthz_status == "ok"
    assert result.readyz_status == "ready"
    assert result.cluster_status == "degraded"
    assert result.unhealthy_count == 2