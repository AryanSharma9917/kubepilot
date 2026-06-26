import pytest

from agent import AgentInput, KubePilotAgent


@pytest.mark.anyio
async def test_agent_returns_placeholder_response() -> None:
    agent = KubePilotAgent()

    output = await agent.run(AgentInput(message="Why is my deployment failing?"))

    assert output.answer == (
        'KubePilot received your question: "Why is my deployment failing?". '
        "Agent integration is not configured yet."
    )
