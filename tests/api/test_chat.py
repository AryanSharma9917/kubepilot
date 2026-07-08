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
    assert body["citations"]
    assert {"title", "source", "snippet"} <= set(body["citations"][0])


@pytest.mark.anyio
async def test_chat_trims_message_whitespace(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={"message": "  Show unhealthy workloads  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert '"Show unhealthy workloads"' in body["answer"]
    assert "payments/deployment/checkout" in body["answer"]
    assert "Unhealthy workloads" in body["sources"]


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


@pytest.mark.anyio
async def test_stream_chat_returns_server_sent_events(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat/stream",
        json={"message": "Why is my deployment failing?"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "event: answer_delta" in response.text
    assert "event: sources" in response.text
    assert "event: citations" in response.text
    assert "event: done" in response.text
