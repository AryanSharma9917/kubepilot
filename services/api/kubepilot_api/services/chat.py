"""Chat application service."""

from uuid import uuid4

from agent import Agent, AgentInput, create_agent
from kubepilot_api.schemas import ChatRequest, ChatResponse


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
        )


async def get_chat_service() -> ChatService:
    """Provide the chat service to API routes."""

    return ChatService()
