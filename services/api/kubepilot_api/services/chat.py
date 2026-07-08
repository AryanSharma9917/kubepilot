"""Chat application service."""

import json
from collections.abc import AsyncIterator
from uuid import uuid4

from agent import Agent, AgentInput, create_agent
from kubepilot_api.schemas import ChatRequest, ChatResponse, CitationResponse


class ChatService:
    """Boundary between the HTTP API and the future agent implementation."""

    def __init__(self, agent: Agent | None = None) -> None:
        self._agent = agent or create_agent()

    async def respond(self, request: ChatRequest) -> ChatResponse:
        """Pass the user request through the KubePilot agent boundary."""

        agent_output = await self._agent.run(AgentInput(message=request.message))

        return ChatResponse(
            request_id=uuid4(),
            answer=agent_output.answer,
            sources=list(agent_output.sources),
            citations=[
                CitationResponse(
                    title=citation.title,
                    source=citation.source,
                    snippet=citation.snippet,
                )
                for citation in agent_output.citations
            ],
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """Stream an agent response as server-sent events."""

        response = await self.respond(request)
        for chunk in _chunks(response.answer):
            yield _event("answer_delta", {"text": chunk})
        yield _event("sources", {"sources": response.sources})
        yield _event(
            "citations",
            {
                "citations": [
                    citation.model_dump(mode="json")
                    for citation in response.citations
                ]
            },
        )
        yield _event("done", {"request_id": str(response.request_id)})


async def get_chat_service() -> ChatService:
    """Provide the chat service to API routes."""

    return ChatService()


def _event(name: str, payload: object) -> str:
    return f"event: {name}\ndata: {json.dumps(payload)}\n\n"


def _chunks(text: str, *, chunk_size: int = 80) -> list[str]:
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
