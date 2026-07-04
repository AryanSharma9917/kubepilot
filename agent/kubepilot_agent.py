"""Initial KubePilot agent boundary."""

import os
import re
from pathlib import Path
from typing import Protocol

from agent.answers import AnswerSynthesizer, GroundedAnswerSynthesizer
from agent.graph.intents import classify_intent
from agent.incidents import IncidentReport, build_deployment_incident_report
from agent.state.chat import AgentInput, AgentOutput
from agent.tools.kubernetes import (
    ClusterHealth,
    ClusterHealthInspector,
    DeploymentDiagnoser,
    DeploymentDiagnosis,
    create_cluster_health_inspector,
    create_deployment_diagnoser,
)
from rag import (
    RetrievedDocument,
    create_default_retriever,
    create_persisted_vector_retriever,
    create_vector_retriever,
)


class Agent(Protocol):
    """Interface implemented by KubePilot agent runtimes."""

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Run the agent for a single user message."""


class Retriever(Protocol):
    """Search interface shared by keyword and vector retrieval."""

    def search(self, query: str, *, limit: int = 3) -> list[RetrievedDocument]:
        """Return matching documents."""


class KubePilotAgent:
    """Deterministic agent shell with simple retrieval and tool routing."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        cluster_inspector: ClusterHealthInspector | None = None,
        deployment_diagnoser: DeploymentDiagnoser | None = None,
        answer_synthesizer: AnswerSynthesizer | None = None,
    ) -> None:
        self._retriever = retriever or create_default_retriever()
        self._cluster_inspector = cluster_inspector or create_cluster_health_inspector()
        self._deployment_diagnoser = deployment_diagnoser or create_deployment_diagnoser()
        self._answer_synthesizer = answer_synthesizer or GroundedAnswerSynthesizer()

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Return a stable response grounded in runbooks or tool output."""

        matches = self._retriever.search(agent_input.message)
        sources = _source_titles(matches)
        intent = classify_intent(agent_input.message)

        if intent.name == "cluster_health":
            cluster_health = await self._cluster_inspector.inspect()
            return AgentOutput(
                answer=_build_cluster_health_answer(agent_input.message, cluster_health),
                sources=sources,
            )

        deployment_ref = _deployment_reference(agent_input.message)
        should_use_deployment_tool = intent.name in {
            "deployment_diagnosis",
            "incident_report",
        }
        if should_use_deployment_tool and deployment_ref is not None:
            namespace, name = deployment_ref
            diagnosis = await self._deployment_diagnoser.diagnose(namespace=namespace, name=name)
            if intent.name == "incident_report" and diagnosis is not None:
                report = build_deployment_incident_report(diagnosis, sources=sources)
                return AgentOutput(
                    answer=_build_incident_report_answer(agent_input.message, report),
                    sources=sources,
                )
            return AgentOutput(
                answer=_build_deployment_diagnosis_answer(agent_input.message, diagnosis),
                sources=sources,
            )

        grounded_answer = await self._answer_synthesizer.synthesize(
            message=agent_input.message,
            matches=matches,
        )
        return AgentOutput(
            answer=grounded_answer.answer,
            sources=grounded_answer.sources,
        )


def create_agent() -> Agent:
    """Create the default KubePilot agent runtime."""

    if os.getenv("KUBEPILOT_AGENT_MODE", "deterministic") == "langgraph":
        from agent.graph.workflow import create_graph_agent

        return create_graph_agent()

    return KubePilotAgent(retriever=_create_retriever())


def _create_retriever() -> Retriever:
    index_path = os.getenv("KUBEPILOT_RAG_INDEX_PATH")
    if index_path:
        return create_persisted_vector_retriever(Path(index_path))
    if os.getenv("KUBEPILOT_RAG_MODE", "keyword") in {"faiss", "vector"}:
        return create_vector_retriever()
    return create_default_retriever()


def _source_titles(matches: list[RetrievedDocument]) -> tuple[str, ...]:
    unique_titles: list[str] = []
    for match in matches:
        title = match.document.title
        if title not in unique_titles:
            unique_titles.append(title)
    return tuple(unique_titles)


def _deployment_reference(message: str) -> tuple[str, str] | None:
    normalized = message.lower()
    if "deployment" not in normalized and "rollout" not in normalized:
        return None
    if not any(
        term in normalized
        for term in ("fail", "failing", "diagnose", "why", "status", "incident")
    ):
        return None

    namespace_match = re.search(r"(?:namespace|ns)\s+([a-z0-9-]+)", normalized)
    name_match = re.search(r"(?:deployment|deploy)\s+([a-z0-9-]+)", normalized)
    candidate = name_match.group(1) if name_match else None
    if candidate in {"fail", "failing", "failed", "status", "diagnose"}:
        candidate = None
    if candidate is None and "checkout" not in normalized:
        return None
    namespace = namespace_match.group(1) if namespace_match else "payments"
    name = candidate if candidate else "checkout"
    return namespace, name


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


def _build_deployment_diagnosis_answer(
    message: str,
    diagnosis: DeploymentDiagnosis | None,
) -> str:
    base_answer = f'KubePilot received your question: "{message}".'
    if diagnosis is None:
        return f"{base_answer} The requested deployment was not found."

    unhealthy_pods = [pod for pod in diagnosis.pods if not pod.ready]
    pod_summary = (
        f"{len(unhealthy_pods)} unhealthy pod(s)"
        if unhealthy_pods
        else "no unhealthy pods found"
    )
    event_summary = (
        f"{len(diagnosis.events)} relevant event(s)"
        if diagnosis.events
        else "no relevant events found"
    )
    log_summary = (
        f"{len(diagnosis.logs)} log excerpt(s)"
        if diagnosis.logs
        else "no log excerpts captured"
    )
    recommendations = " ".join(diagnosis.recommendations)
    return (
        f"{base_answer} Deployment {diagnosis.display_name} is "
        f"{diagnosis.health.status.lower()}: {diagnosis.health.reason}. "
        f"Found {pod_summary}, {event_summary}, and {log_summary}. Recommended next step: "
        f"{recommendations}"
    )


def _build_incident_report_answer(message: str, report: IncidentReport) -> str:
    base_answer = f'KubePilot received your question: "{message}".'
    evidence_summary = "; ".join(item.message for item in report.evidence[:3])
    next_actions = " ".join(report.next_actions)
    return (
        f"{base_answer} {report.title}. Severity: {report.severity}. "
        f"Summary: {report.summary} Evidence: {evidence_summary}. "
        f"Next actions: {next_actions}"
    )
