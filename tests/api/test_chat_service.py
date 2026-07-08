from uuid import UUID

import pytest
from kubepilot_api.schemas import ChatRequest
from kubepilot_api.services.chat import ChatService

from agent import AgentInput, AgentOutput
from agent.state.chat import Citation


class FakeAgent:
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        assert agent_input.message == "Show unhealthy workloads"
        return AgentOutput(
            answer="fake agent answer",
            sources=("Unhealthy workloads",),
            citations=(
                Citation(
                    title="Unhealthy workloads",
                    source="unhealthy.md",
                    snippet="List degraded deployments.",
                ),
            ),
        )


@pytest.mark.anyio
async def test_chat_service_uses_agent_boundary() -> None:
    service = ChatService(agent=FakeAgent())

    response = await service.respond(ChatRequest(message="Show unhealthy workloads"))

    assert isinstance(response.request_id, UUID)
    assert response.answer == "fake agent answer"
    assert response.sources == ["Unhealthy workloads"]
    assert response.citations[0].source == "unhealthy.md"
