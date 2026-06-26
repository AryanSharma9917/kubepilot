"""Chat application service."""

from uuid import uuid4

from kubepilot_api.schemas import ChatRequest, ChatResponse


class ChatService:
    """Boundary between the HTTP API and the future agent implementation."""

    async def respond(self, request: ChatRequest) -> ChatResponse:
        """Return a placeholder response until the agent is connected."""

        return ChatResponse(
            request_id=uuid4(),
            answer=(
                f'KubePilot received your question: "{request.message}". '
                "Agent integration is not configured yet."
            ),
        )


async def get_chat_service() -> ChatService:
    """Provide the chat service to API routes."""

    return ChatService()
