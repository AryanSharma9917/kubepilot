"""LangGraph-oriented agent workflow boundary."""

from dataclasses import dataclass
from typing import Any

from agent.graph.intents import Intent, classify_intent
from agent.kubepilot_agent import KubePilotAgent
from agent.state.chat import AgentInput, AgentOutput


@dataclass
class WorkflowStep:
    """One logical step in an agent workflow."""

    name: str
    description: str


@dataclass
class GraphState:
    """State passed through graph execution."""

    message: str
    intent: Intent | None = None
    route: str | None = None
    steps: tuple[WorkflowStep, ...] = ()
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

        result = await self._graph.ainvoke(
            {
                "message": agent_input.message,
                "intent": None,
                "route": None,
                "steps": (),
                "output": None,
            }
        )
        output = result.get("output")
        if isinstance(output, AgentOutput):
            return output
        return await self._fallback_agent.run(agent_input)

    def _build_graph(self) -> Any | None:
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return None

        def classify(state: dict[str, Any]) -> dict[str, Any]:
            intent = classify_intent(state["message"])
            return {
                **state,
                "intent": intent,
                "route": intent.name,
                "steps": build_workflow_steps(intent),
            }

        async def execute(state: dict[str, Any]) -> dict[str, Any]:
            output = await self._fallback_agent.run(AgentInput(message=state["message"]))
            return {**state, "output": output}

        graph = StateGraph(dict)
        graph.add_node("classify_intent", classify)
        graph.add_node("execute_tools_and_synthesize", execute)
        graph.set_entry_point("classify_intent")
        graph.add_edge("classify_intent", "execute_tools_and_synthesize")
        graph.add_edge("execute_tools_and_synthesize", END)
        return graph.compile()


def create_graph_agent() -> GraphAgent:
    """Create the graph-backed agent runtime."""

    return GraphAgent()


def build_workflow_steps(intent: Intent) -> tuple[WorkflowStep, ...]:
    """Return the logical workflow steps for an intent."""

    common = (
        WorkflowStep("classify_intent", "Classify the user request."),
        WorkflowStep("retrieve_context", "Retrieve relevant runbook context."),
    )
    if intent.name == "cluster_health":
        return common + (
            WorkflowStep("inspect_cluster", "Collect workload health signals."),
            WorkflowStep("summarize_health", "Summarize unhealthy workloads."),
        )
    if intent.name == "deployment_diagnosis":
        return common + (
            WorkflowStep("diagnose_deployment", "Collect deployment, pod, event, and log signals."),
            WorkflowStep("synthesize_diagnosis", "Produce operator-focused next steps."),
        )
    if intent.name == "incident_report":
        return common + (
            WorkflowStep("diagnose_deployment", "Collect deployment incident evidence."),
            WorkflowStep("build_incident_report", "Create a structured incident report."),
        )
    return common + (
        WorkflowStep("synthesize_answer", "Generate a grounded runbook answer."),
    )
