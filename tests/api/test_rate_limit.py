import httpx
import pytest
from kubepilot_api.config import get_settings
from kubepilot_api.main import create_app
from kubepilot_api.rate_limit import REQUEST_TIMESTAMPS


@pytest.mark.anyio
async def test_rate_limit_is_disabled_by_default(client: httpx.AsyncClient) -> None:
    first = await client.post("/api/v1/chat", json={"message": "hello"})
    second = await client.post("/api/v1/chat", json={"message": "hello again"})

    assert first.status_code == 200
    assert second.status_code == 200


@pytest.mark.anyio
async def test_rate_limit_rejects_api_requests_after_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KUBEPILOT_RATE_LIMIT_PER_MINUTE", "1")
    get_settings.cache_clear()
    REQUEST_TIMESTAMPS.clear()

    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/api/v1/chat", json={"message": "hello"})
        second = await client.post("/api/v1/chat", json={"message": "hello again"})
        health = await client.get("/healthz")

    get_settings.cache_clear()
    REQUEST_TIMESTAMPS.clear()

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json() == {"detail": "Rate limit exceeded"}
    assert second.headers["retry-after"] == "60"
    assert health.status_code == 200
