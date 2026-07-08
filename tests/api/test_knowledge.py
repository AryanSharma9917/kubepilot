import httpx
import pytest


@pytest.mark.anyio
async def test_knowledge_search_returns_ranked_results(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "deployment image pull failing", "limit": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert {"title", "source", "snippet", "score"} <= set(body["results"][0])


@pytest.mark.anyio
async def test_knowledge_search_rejects_blank_query(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/knowledge/search",
        json={"query": "   "},
    )

    assert response.status_code == 422
