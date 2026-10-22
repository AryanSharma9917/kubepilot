import json
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


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("namespace", "deployment"),
    [("payments", "checkout"), ("notifications", "email-worker"), ("platform", "metrics-scraper")],
)
async def test_chat_uses_explicit_workload_context(
    client: httpx.AsyncClient, namespace: str, deployment: str
) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={
            "message": "Why is this failing?",
            "workload": {"namespace": namespace, "deployment": deployment},
        },
    )

    assert response.status_code == 200
    assert f"{namespace}/deployment/{deployment}" in response.json()["answer"]
    assert "Evidence:" in response.json()["answer"]


@pytest.mark.anyio
async def test_contextual_stream_uses_selected_workload(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat/stream",
        json={
            "message": "Why is this failing?",
            "workload": {"namespace": "notifications", "deployment": "email-worker"},
        },
    )

    assert response.status_code == 200
    chunks = [
        json.loads(event.split("data: ", 1)[1])["text"]
        for event in response.text.split("\n\n")
        if event.startswith("event: answer_delta\n")
    ]
    assert "notifications/deployment/email-worker" in "".join(chunks)
    assert "event: done" in response.text


@pytest.mark.anyio
async def test_context_does_not_fall_back_to_known_fixture(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={
            "message": "Why is checkout failing?",
            "workload": {"namespace": "other", "deployment": "checkout.v2"},
        },
    )

    assert response.status_code == 200
    assert "deployment checkout.v2 in namespace other" in response.json()["answer"]
    assert "requested deployment was not found" in response.json()["answer"]


@pytest.mark.anyio
@pytest.mark.parametrize("namespace", ["", "Bad Namespace", "payments/other"])
async def test_chat_rejects_invalid_workload_context(
    client: httpx.AsyncClient, namespace: str
) -> None:
    response = await client.post(
        "/api/v1/chat",
        json={"message": "Why?", "workload": {"namespace": namespace, "deployment": "checkout"}},
    )

    assert response.status_code == 422
