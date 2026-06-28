from uuid import UUID

import httpx
import pytest


@pytest.mark.anyio
async def test_chat_returns_placeholder_response(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={"message": "Why is my deployment failing?"},
    )

    assert response.status_code == 200
    body = response.json()
    assert UUID(body["request_id"])
    assert body["answer"].startswith(
        'KubePilot received your question: "Why is my deployment failing?".'
    )
    assert body["sources"]


@pytest.mark.anyio
async def test_chat_trims_message_whitespace(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={"message": "  Show unhealthy workloads  "},
    )

    assert response.status_code == 200
    assert '"Show unhealthy workloads"' in response.json()["answer"]
    assert "Unhealthy workloads" in response.json()["sources"]


@pytest.mark.anyio
async def test_chat_rejects_blank_message(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/chat", json={"message": "   "})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_chat_rejects_missing_message(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/chat", json={})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_chat_rejects_message_over_limit(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/chat", json={"message": "x" * 4001})

    assert response.status_code == 422
