"""LangGraph-oriented agent workflow boundary."""

from dataclasses import dataclass
from typing import Any

from agent.graph.intents import Intent, classify_intent
from agent.kubepilot_agent import KubePilotAgent
from agent.state.chat import AgentInput, AgentOutput
from agent.tools.kubernetes import ClusterHealth, DeploymentDiagnosis
from rag import RetrievedDocument


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
    matches: list[RetrievedDocument] | None = None
    deployment_ref: tuple[str, str] | None = None
    cluster_health: ClusterHealth | None = None
    diagnosis: DeploymentDiagnosis | None = None
    output: AgentOutput | None = None
    reviewed: bool = False


class GraphAgent:
    """Agent runtime that can use LangGraph when the dependency is available."""

    def __init__(self, fallback_agent: KubePilotAgent | None = None) -> None:
        self._fallback_agent = fallback_agent or KubePilotAgent()
        self._operation_agent = (
            self._fallback_agent
            if isinstance(self._fallback_agent, KubePilotAgent)
            else None
        )
        self._graph = self._build_graph()

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Run the graph workflow for one user message."""

        initial_state = {
            "message": agent_input.message,
            "intent": None,
            "route": None,
            "steps": (),
            "matches": None,
            "deployment_ref": None,
            "cluster_health": None,
            "diagnosis": None,
            "output": None,
            "reviewed": False,
        }
        if self._graph is None:
            if self._operation_agent is None:
                return await self._fallback_agent.run(agent_input)
            result = await self._run_state_machine(initial_state)
        else:
            result = await self._graph.ainvoke(initial_state)

        output = result.get("output")
        if review_agent_output(output):
            return output
        return await self._fallback_agent.run(agent_input)

    async def _run_state_machine(self, state: dict[str, Any]) -> dict[str, Any]:
        state = self._classify_intent(state)
        state = self._retrieve_context(state)
        route = self._route_after_retrieval(state)
        if route == "inspect_cluster":
            state = await self._inspect_cluster(state)
            state = await self._summarize_health(state)
        elif route == "diagnose_deployment":
            state = await self._diagnose_deployment(state)
            state = await self._synthesize_diagnosis(state)
        elif route == "build_incident_report":
            state = await self._diagnose_deployment(state)
            state = await self._build_incident_report(state)
        else:
            state = await self._synthesize_answer(state)
        return self._review_output(state)

    def _build_graph(self) -> Any | None:
        if self._operation_agent is None:
            return None
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return None

        graph = StateGraph(dict)
        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("inspect_cluster", self._inspect_cluster)
        graph.add_node("summarize_health", self._summarize_health)
        graph.add_node("diagnose_deployment", self._diagnose_deployment)
        graph.add_node("synthesize_diagnosis", self._synthesize_diagnosis)
        graph.add_node("build_incident_report", self._build_incident_report)
        graph.add_node("synthesize_answer", self._synthesize_answer)
        graph.add_node("review_output", self._review_output)
        graph.set_entry_point("classify_intent")
        graph.add_edge("classify_intent", "retrieve_context")
        graph.add_conditional_edges(
            "retrieve_context",
            self._route_after_retrieval,
            {
                "inspect_cluster": "inspect_cluster",
                "diagnose_deployment": "diagnose_deployment",
                "build_incident_report": "diagnose_deployment",
                "synthesize_answer": "synthesize_answer",
            },
        )
        graph.add_edge("inspect_cluster", "summarize_health")
        graph.add_edge("summarize_health", "review_output")
        graph.add_conditional_edges(
            "diagnose_deployment",
            self._route_after_diagnosis,
            {
                "synthesize_diagnosis": "synthesize_diagnosis",
                "build_incident_report": "build_incident_report",
            },
        )
        graph.add_edge("synthesize_diagnosis", "review_output")
        graph.add_edge("build_incident_report", "review_output")
        graph.add_edge("synthesize_answer", "review_output")
        graph.add_edge("review_output", END)
        return graph.compile()

    def _classify_intent(self, state: dict[str, Any]) -> dict[str, Any]:
        intent = classify_intent(state["message"])
        return {
            **state,
            "intent": intent,
            "route": intent.name,
            "steps": build_workflow_steps(intent),
        }

    def _retrieve_context(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            **state,
            "matches": self._operation_agent.retrieve_context(state["message"]),
            "deployment_ref": self._operation_agent.deployment_reference(state["message"]),
        }

    def _route_after_retrieval(self, state: dict[str, Any]) -> str:
        intent = state.get("intent")
        if not isinstance(intent, Intent):
            return "synthesize_answer"
        if intent.name == "cluster_health":
            return "inspect_cluster"
        if state.get("deployment_ref") is None:
            return "synthesize_answer"
        if intent.name == "incident_report":
            return "build_incident_report"
        if intent.name == "deployment_diagnosis":
            return "diagnose_deployment"
        return "synthesize_answer"

    async def _inspect_cluster(self, state: dict[str, Any]) -> dict[str, Any]:
        return {**state, "cluster_health": await self._operation_agent.inspect_cluster_health()}

    async def _summarize_health(self, state: dict[str, Any]) -> dict[str, Any]:
        output = await self._operation_agent.answer_cluster_health(
            state["message"],
            state.get("matches") or [],
            state.get("cluster_health"),
        )
        return {**state, "output": output}

    async def _diagnose_deployment(self, state: dict[str, Any]) -> dict[str, Any]:
        deployment_ref = state.get("deployment_ref")
        if deployment_ref is None:
            return state
        namespace, name = deployment_ref
        diagnosis = await self._fallback_agent.diagnose_deployment(
            namespace=namespace,
            name=name,
        )
        return {**state, "diagnosis": diagnosis}

    def _route_after_diagnosis(self, state: dict[str, Any]) -> str:
        intent = state.get("intent")
        if isinstance(intent, Intent) and intent.name == "incident_report":
            return "build_incident_report"
        return "synthesize_diagnosis"

    async def _synthesize_diagnosis(self, state: dict[str, Any]) -> dict[str, Any]:
        deployment_ref = state.get("deployment_ref")
        if deployment_ref is None:
            return await self._synthesize_answer(state)
        namespace, name = deployment_ref
        output = await self._operation_agent.answer_deployment_diagnosis(
            state["message"],
            state.get("matches") or [],
            namespace=namespace,
            name=name,
            diagnosis=state.get("diagnosis"),
        )
        return {**state, "output": output}

    async def _build_incident_report(self, state: dict[str, Any]) -> dict[str, Any]:
        deployment_ref = state.get("deployment_ref")
        if deployment_ref is None:
            return await self._synthesize_answer(state)
        namespace, name = deployment_ref
        output = await self._operation_agent.answer_incident_report(
            state["message"],
            state.get("matches") or [],
            namespace=namespace,
            name=name,
            diagnosis=state.get("diagnosis"),
        )
        return {**state, "output": output}

    async def _synthesize_answer(self, state: dict[str, Any]) -> dict[str, Any]:
        output = await self._operation_agent.answer_runbook(
            state["message"],
            state.get("matches") or [],
        )
        return {**state, "output": output}

    def _review_output(self, state: dict[str, Any]) -> dict[str, Any]:
        output = state.get("output")
        if not review_agent_output(output):
            return {**state, "output": None, "reviewed": False}
        return {**state, "reviewed": True}


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
            WorkflowStep("review_output", "Verify the final response is usable."),
        )
    if intent.name == "deployment_diagnosis":
        return common + (
            WorkflowStep("diagnose_deployment", "Collect deployment, pod, event, and log signals."),
            WorkflowStep("synthesize_diagnosis", "Produce operator-focused next steps."),
            WorkflowStep("review_output", "Verify the final response is usable."),
        )
    if intent.name == "incident_report":
        return common + (
            WorkflowStep("diagnose_deployment", "Collect deployment incident evidence."),
            WorkflowStep("build_incident_report", "Create a structured incident report."),
            WorkflowStep("review_output", "Verify the final response is usable."),
        )
    return common + (
        WorkflowStep("synthesize_answer", "Generate a grounded runbook answer."),
        WorkflowStep("review_output", "Verify the final response is usable."),
    )


def review_agent_output(output: AgentOutput | None) -> bool:
    """Return whether an agent output is suitable to return to users."""

    return isinstance(output, AgentOutput) and bool(output.answer.strip())
