import httpx
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
