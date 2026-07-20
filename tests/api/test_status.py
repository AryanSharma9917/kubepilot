import httpx
import pytest
from kubepilot_api.config import get_settings
from kubepilot_api.main import create_app


@pytest.mark.anyio
async def test_runtime_status_returns_redacted_defaults(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/status")

    assert response.status_code == 200
    body = response.json()
    assert body["environment"] == "development"
    assert body["kubernetes_mode"] == "fixture"
    assert body["rag_mode"] == "keyword"
    assert body["auth_enabled"] is False
    assert body["namespace_policy_enabled"] is False
    assert body["action_policy_enabled"] is False
    assert body["rate_limit_per_minute"] == 0
    assert body["otel_export_enabled"] is False
    assert "api_keys" not in body


@pytest.mark.anyio
async def test_runtime_status_reflects_enabled_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KUBEPILOT_ENVIRONMENT", "staging")
    monkeypatch.setenv("KUBEPILOT_API_KEYS", "secret")
    monkeypatch.setenv("KUBEPILOT_ALLOWED_NAMESPACES", "payments")
    monkeypatch.setenv("KUBEPILOT_ALLOWED_ACTIONS", "cluster:health")
    monkeypatch.setenv("KUBEPILOT_RATE_LIMIT_PER_MINUTE", "10")
    monkeypatch.setenv(
        "KUBEPILOT_OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector:4318/v1/traces",
    )
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/status",
            headers={"authorization": "Bearer secret"},
        )

    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["environment"] == "staging"
    assert body["auth_enabled"] is True
    assert body["namespace_policy_enabled"] is True
    assert body["action_policy_enabled"] is True
    assert body["rate_limit_per_minute"] == 10
    assert body["otel_export_enabled"] is True
