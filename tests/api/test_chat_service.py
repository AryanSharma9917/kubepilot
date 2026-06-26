from uuid import UUID

import pytest
from kubepilot_api.schemas import ChatRequest
from kubepilot_api.services.chat import ChatService

from agent import AgentInput, AgentOutput


class FakeAgent:
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        assert agent_input.message == "Show unhealthy workloads"
        return AgentOutput(answer="fake agent answer")


@pytest.mark.anyio
async def test_chat_service_uses_agent_boundary() -> None:
    service = ChatService(agent=FakeAgent())

    response = await service.respond(ChatRequest(message="Show unhealthy workloads"))

    assert isinstance(response.request_id, UUID)
    assert response.answer == "fake agent answer"
