import httpx
import kubepilot_api.auth as auth
import pytest
from kubepilot_api.config import get_settings
from kubepilot_api.main import create_app


@pytest.mark.anyio
async def test_api_key_auth_is_disabled_by_default(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/chat", json={"message": "hello"})

    assert response.status_code == 200


@pytest.mark.anyio
async def test_api_key_auth_rejects_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KUBEPILOT_API_KEYS", "secret")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"message": "hello"})

    get_settings.cache_clear()

    assert response.status_code == 401


@pytest.mark.anyio
async def test_api_key_auth_accepts_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KUBEPILOT_API_KEYS", "secret")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "hello"},
            headers={"authorization": "Bearer secret"},
        )

    get_settings.cache_clear()

    assert response.status_code == 200


@pytest.mark.anyio
async def test_oidc_rejects_api_key_when_oidc_is_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KUBEPILOT_API_KEYS", "secret")
    monkeypatch.setenv("KUBEPILOT_OIDC_ISSUER", "https://issuer.example.com")
    monkeypatch.setenv("KUBEPILOT_OIDC_REQUIRED", "true")
    get_settings.cache_clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/status",
            headers={"x-api-key": "secret"},
        )

    get_settings.cache_clear()

    assert response.status_code == 401


@pytest.mark.anyio
async def test_oidc_role_policy_allows_configured_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KUBEPILOT_OIDC_ISSUER", "https://issuer.example.com")
    monkeypatch.setenv("KUBEPILOT_OIDC_AUDIENCE", "kubepilot-api")
    monkeypatch.setenv("KUBEPILOT_OIDC_ROLE_ACTIONS", "read-only=system:read")
    get_settings.cache_clear()
    monkeypatch.setattr(
        auth,
        "_decode_oidc_token",
        lambda token, settings: {"roles": ["read-only"]},
    )

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/status",
            headers={"authorization": "Bearer signed-token"},
        )

    get_settings.cache_clear()

    assert response.status_code == 200


@pytest.mark.anyio
async def test_oidc_role_policy_rejects_unconfigured_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KUBEPILOT_OIDC_ISSUER", "https://issuer.example.com")
    monkeypatch.setenv("KUBEPILOT_OIDC_AUDIENCE", "kubepilot-api")
    monkeypatch.setenv("KUBEPILOT_OIDC_ROLE_ACTIONS", "read-only=cluster:health")
    get_settings.cache_clear()
    monkeypatch.setattr(
        auth,
        "_decode_oidc_token",
        lambda token, settings: {"roles": ["read-only"]},
    )

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/status",
            headers={"authorization": "Bearer signed-token"},
        )

    get_settings.cache_clear()

    assert response.status_code == 403
