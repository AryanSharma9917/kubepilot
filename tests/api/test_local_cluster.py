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
    if request.url.path == "/api/v1/capabilities":
        return httpx.Response(
            200,
            json={
                "capabilities": [
                    {"name": "Agentic orchestration", "status": "deterministic", "description": ""},
                    {"name": "Runbook RAG", "status": "keyword", "description": ""},
                    {"name": "Kubernetes diagnosis", "status": "fixture", "description": ""},
                    {"name": "Incident reporting", "status": "ready", "description": ""},
                    {"name": "Observability", "status": "ready", "description": ""},
                    {"name": "Platform deployment", "status": "ready", "description": ""},
                ]
            },
        )
    if request.url.path == "/api/v1/chat":
        return httpx.Response(
            200,
            json={
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "answer": (
                    'KubePilot received your question: "Show unhealthy workloads". '
                    "Unhealthy workloads: payments/deployment/checkout has 1/3 replicas ready."
                ),
                "sources": ["Unhealthy workloads"],
            },
        )
    diagnosis_path = "/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose"
    if request.url.path == diagnosis_path:
        return httpx.Response(
            200,
            json={
                "namespace": "payments",
                "name": "checkout",
                "health": {
                    "namespace": "payments",
                    "name": "checkout",
                    "kind": "Deployment",
                    "desired_replicas": 3,
                    "ready_replicas": 1,
                    "status": "Degraded",
                    "reason": "Two replicas are unavailable",
                },
                "pods": [],
                "events": [],
                "logs": [],
                "recommendations": ["Inspect the latest events."],
            },
        )
    incident_report_path = (
        "/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report"
    )
    if request.url.path == incident_report_path:
        return httpx.Response(
            200,
            json={
                "report_id": "incident-demo-1",
                "generated_at": "2026-08-04T00:00:00Z",
                "title": "Deployment incident: payments/deployment/checkout",
                "severity": "critical",
                "summary": "The checkout deployment is not fully available.",
                "probable_cause": "Readiness probe failure.",
                "operator_impact": "Checkout is partially unavailable.",
                "impacted_resource": "payments/deployment/checkout",
                "evidence": [],
                "timeline": [],
                "next_actions": ["Investigate pod failures."],
                "status_update": "CRITICAL: checkout is degraded.",
                "sources": ["Deployment rollout failures"],
            },
        )
    remediation_path = (
        "/api/v1/cluster/namespaces/payments/deployments/checkout/remediation-plan"
    )
    if request.url.path == remediation_path:
        return httpx.Response(
            200,
            json={
                "namespace": "payments",
                "name": "checkout",
                "summary": "Review and approve before running commands.",
                "approval_required": True,
                "actions": [
                    {
                        "title": "Capture rollout evidence",
                        "command": "kubectl describe deployment/checkout -n payments",
                        "risk": "low",
                        "requires_approval": True,
                        "reason": "Read-only evidence capture.",
                    }
                ],
                "rollback": "kubectl rollout undo deployment/checkout -n payments",
            },
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
    assert result.capability_count == 6
    assert result.remediation_action_count == 1
