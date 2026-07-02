"""LangGraph-oriented agent workflow boundary."""

from dataclasses import dataclass
from typing import Any

from agent.kubepilot_agent import KubePilotAgent
from agent.state.chat import AgentInput, AgentOutput


@dataclass
class GraphState:
    """State passed through graph execution."""

    message: str
    output: AgentOutput | None = None


class GraphAgent:
    """Agent runtime that can use LangGraph when the dependency is available."""

    def __init__(self, fallback_agent: KubePilotAgent | None = None) -> None:
        self._fallback_agent = fallback_agent or KubePilotAgent()
        self._graph = self._build_graph()

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Run the graph workflow for one user message."""

        if self._graph is None:
            return await self._fallback_agent.run(agent_input)

        result = await self._graph.ainvoke({"message": agent_input.message, "output": None})
        output = result.get("output")
        if isinstance(output, AgentOutput):
            return output
        return await self._fallback_agent.run(agent_input)

    def _build_graph(self) -> Any | None:
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return None

        async def run_agent(state: dict[str, Any]) -> dict[str, Any]:
            output = await self._fallback_agent.run(AgentInput(message=state["message"]))
            return {"message": state["message"], "output": output}

        graph = StateGraph(dict)
        graph.add_node("agent", run_agent)
        graph.set_entry_point("agent")
        graph.add_edge("agent", END)
        return graph.compile()


def create_graph_agent() -> GraphAgent:
    """Create the graph-backed agent runtime."""

    return GraphAgent()
