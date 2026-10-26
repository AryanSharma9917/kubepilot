"""Policy checks cover the HTTP boundary and actual agent tool calls."""

import httpx
import pytest
from kubepilot_api.config import get_settings
from kubepilot_api.incident_store import InMemoryIncidentReportStore
from kubepilot_api.main import create_app

from agent.tools.kubernetes.client import create_fixture_kubernetes_client


@pytest.fixture(autouse=True)
def reset_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.anyio
@pytest.mark.parametrize("runtime", ["deterministic", "langgraph"])
async def test_scoped_overview_and_chat_never_request_cluster_wide_reads(monkeypatch, runtime):
    fixture = create_fixture_kubernetes_client()
    calls = []

    class NamespacedOnlyClient:
        async def list_deployments(self, namespace=None):
            assert namespace is not None, "Cluster-wide list would require broader RBAC"
            calls.append(namespace)
            # Deliberately return excess data to verify defensive filtering as well.
            return await fixture.list_deployments()

    monkeypatch.setenv("KUBEPILOT_K8S_MODE", "service")
    monkeypatch.setenv("KUBEPILOT_AGENT_MODE", runtime)
    monkeypatch.setenv("KUBEPILOT_ALLOWED_NAMESPACES", "platform,platform")
    monkeypatch.setattr(
        "agent.tools.kubernetes.client.KubernetesServiceClient", lambda url: NamespacedOnlyClient()
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/cluster/health")
        assert response.status_code == 200
        assert {item["namespace"] for item in response.json()["workloads"]} == {"platform"}
        chat = await client.post("/api/v1/chat", json={"message": "Show unhealthy workloads"})
        assert chat.status_code == 200
        assert "metrics-scraper" in chat.json()["answer"]
        assert "checkout" not in chat.json()["answer"]
    assert calls == ["platform", "platform"]


@pytest.mark.anyio
@pytest.mark.parametrize("runtime", ["deterministic", "langgraph"])
@pytest.mark.parametrize("endpoint", ["/api/v1/chat", "/api/v1/chat/stream"])
@pytest.mark.parametrize("explicit_context", [False, True])
async def test_chat_rejects_outside_namespace_before_tools_or_stream(
    monkeypatch, runtime, endpoint, explicit_context
):
    monkeypatch.setenv("KUBEPILOT_AGENT_MODE", runtime)
    monkeypatch.setenv("KUBEPILOT_ALLOWED_NAMESPACES", "payments")
    message = "Why is deployment metrics-scraper failing in namespace platform?"
    payload = {"message": message}
    if explicit_context:
        payload = {
            "message": "Why is this failing?",
            "workload": {"namespace": "platform", "deployment": "metrics-scraper"},
        }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.post(endpoint, json=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Namespace is not allowed: platform"
    assert "text/event-stream" not in response.headers["content-type"]


@pytest.mark.anyio
@pytest.mark.parametrize("endpoint", ["/api/v1/chat", "/api/v1/chat/stream"])
async def test_chat_respects_action_policy(monkeypatch, endpoint):
    monkeypatch.setenv("KUBEPILOT_ALLOWED_ACTIONS", "deployment:diagnose")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        response = await client.post(endpoint, json={"message": "Show unhealthy workloads"})
        runbook = await client.post(endpoint, json={"message": "How do image pull secrets work?"})
    assert response.status_code == 403
    assert runbook.status_code == 200


@pytest.mark.anyio
async def test_saved_report_scope_applies_before_limit_and_to_detail_and_exports(monkeypatch):
    store = InMemoryIncidentReportStore()
    monkeypatch.setattr("kubepilot_api.routes.cluster.get_incident_report_store", lambda: store)
    monkeypatch.setattr("kubepilot_api.services.cluster.get_incident_report_store", lambda: store)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        allowed = (await client.get(
            "/api/v1/cluster/namespaces/payments/deployments/checkout/incident-report"
        )).json()
        denied = (await client.get(
            "/api/v1/cluster/namespaces/platform/deployments/metrics-scraper/incident-report"
        )).json()
        monkeypatch.setenv("KUBEPILOT_ALLOWED_NAMESPACES", "payments")
        get_settings.cache_clear()
        listed = await client.get("/api/v1/cluster/incident-reports?limit=1")
        assert [item["report_id"] for item in listed.json()["reports"]] == [allowed["report_id"]]
        for suffix in ["", "/markdown"]:
            assert (await client.get(
                f"/api/v1/cluster/incident-reports/{denied['report_id']}{suffix}"
            )).status_code == 403
            assert (await client.get(
                f"/api/v1/cluster/incident-reports/{allowed['report_id']}{suffix}"
            )).status_code == 200
        for operation in ["diagnose", "incident-report", "incident-report.md", "remediation-plan"]:
            response = await client.get(
                f"/api/v1/cluster/namespaces/platform/deployments/metrics-scraper/{operation}"
            )
            assert response.status_code == 403


@pytest.mark.anyio
@pytest.mark.parametrize("runtime", ["deterministic", "langgraph"])
async def test_allowed_diagnosis_and_chat_use_configured_service(monkeypatch, runtime):
    from dataclasses import replace

    fixture = create_fixture_kubernetes_client()
    reads = []

    class ConfiguredService:
        def __getattr__(self, name):
            return getattr(fixture, name)

        async def get_deployment(self, namespace, name):
            reads.append((namespace, name))
            workload = await fixture.get_deployment(namespace=namespace, name=name)
            return replace(workload, reason="Configured inspection service evidence")

    monkeypatch.setenv("KUBEPILOT_K8S_MODE", "service")
    monkeypatch.setenv("KUBEPILOT_AGENT_MODE", runtime)
    monkeypatch.setenv("KUBEPILOT_ALLOWED_NAMESPACES", "payments")
    monkeypatch.setattr(
        "agent.tools.kubernetes.client.KubernetesServiceClient", lambda url: ConfiguredService()
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app()), base_url="http://test"
    ) as client:
        diagnosis = await client.get(
            "/api/v1/cluster/namespaces/payments/deployments/checkout/diagnose"
        )
        assert diagnosis.status_code == 200
        assert diagnosis.json()["health"]["reason"] == "Configured inspection service evidence"
        assert diagnosis.json()["logs"]
        chat = await client.post("/api/v1/chat", json={"message": "Why is checkout failing?"})
        assert chat.status_code == 200
        assert "Configured inspection service evidence" in chat.json()["answer"]
    assert reads == [("payments", "checkout"), ("payments", "checkout")]
