"""Initial KubePilot agent boundary."""

from typing import Protocol

from agent.state.chat import AgentInput, AgentOutput


class Agent(Protocol):
    """Interface implemented by KubePilot agent runtimes."""

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Run the agent for a single user message."""


class KubePilotAgent:
    """Deterministic placeholder agent until LangGraph is introduced."""

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Return a stable response while the real agent graph is built."""

        return AgentOutput(
            answer=(
                f'KubePilot received your question: "{agent_input.message}". '
                "Agent integration is not configured yet."
            ),
        )


def create_agent() -> Agent:
    """Create the default KubePilot agent runtime."""

    return KubePilotAgent()
