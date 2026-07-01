"""Initial KubePilot agent boundary."""

from typing import Protocol

from agent.state.chat import AgentInput, AgentOutput
from agent.tools.kubernetes import (
    ClusterHealth,
    ClusterHealthInspector,
    create_cluster_health_inspector,
)
from rag import KeywordRetriever, RetrievedDocument, create_default_retriever


class Agent(Protocol):
    """Interface implemented by KubePilot agent runtimes."""

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Run the agent for a single user message."""


class KubePilotAgent:
    """Deterministic agent shell with simple retrieval and tool routing."""

    def __init__(
        self,
        retriever: KeywordRetriever | None = None,
        cluster_inspector: ClusterHealthInspector | None = None,
    ) -> None:
        self._retriever = retriever or create_default_retriever()
        self._cluster_inspector = cluster_inspector or create_cluster_health_inspector()

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Return a stable response grounded in runbooks or tool output."""

        matches = self._retriever.search(agent_input.message)
        sources = _source_titles(matches)

        if _should_inspect_cluster(agent_input.message):
            cluster_health = await self._cluster_inspector.inspect()
            return AgentOutput(
                answer=_build_cluster_health_answer(agent_input.message, cluster_health),
                sources=sources,
            )

        return AgentOutput(
            answer=_build_answer(agent_input.message, sources),
            sources=sources,
        )


def create_agent() -> Agent:
    """Create the default KubePilot agent runtime."""

    return KubePilotAgent()


def _source_titles(matches: list[RetrievedDocument]) -> tuple[str, ...]:
    unique_titles: list[str] = []
    for match in matches:
        title = match.document.title
        if title not in unique_titles:
            unique_titles.append(title)
    return tuple(unique_titles)


def _build_answer(message: str, sources: tuple[str, ...]) -> str:
    base_answer = f'KubePilot received your question: "{message}".'

    if not sources:
        return f"{base_answer} No matching runbook was found yet."

    source_list = ", ".join(sources)
    return f"{base_answer} Relevant runbooks: {source_list}."


def _should_inspect_cluster(message: str) -> bool:
    normalized = message.lower()
    return (
        "unhealthy workload" in normalized
        or "cluster health" in normalized
        or "unhealthy pod" in normalized
    )


def _build_cluster_health_answer(message: str, cluster_health: ClusterHealth) -> str:
    base_answer = f'KubePilot received your question: "{message}".'
    unhealthy = cluster_health.unhealthy_workloads

    if not unhealthy:
        return f"{base_answer} No unhealthy workloads were found."

    findings = "; ".join(
        (
            f"{workload.display_name} has {workload.ready_replicas}/"
            f"{workload.desired_replicas} replicas ready ({workload.reason})"
        )
        for workload in unhealthy
    )
    return f"{base_answer} Unhealthy workloads: {findings}."
