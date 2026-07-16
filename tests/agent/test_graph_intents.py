import pytest

from agent import KubePilotAgent
from agent.graph import classify_intent
from agent.graph.workflow import GraphAgent, build_workflow_steps, review_agent_output
from agent.state.chat import AgentInput, AgentOutput
from agent.tools.kubernetes import (
    ClusterHealth,
    ContainerLog,
    DeploymentDiagnosis,
    KubernetesEvent,
    PodStatus,
    WorkloadHealth,
)
from rag.models import Document
from rag.retrieval import KeywordRetriever


class EchoAgent:
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(answer=f"echo: {agent_input.message}", sources=())


class FakeClusterInspector:
    async def inspect(self, namespace: str | None = None) -> ClusterHealth:
        assert namespace is None
        return ClusterHealth(
            workloads=(
                WorkloadHealth(
                    namespace="payments",
                    name="checkout",
                    kind="Deployment",
                    desired_replicas=3,
                    ready_replicas=1,
                    status="Degraded",
                    reason="Two replicas are unavailable",
                ),
            ),
        )


class FakeDeploymentDiagnoser:
    async def diagnose(self, namespace: str, name: str) -> DeploymentDiagnosis | None:
        assert namespace == "payments"
        assert name == "checkout"
        return DeploymentDiagnosis(
            namespace="payments",
            name="checkout",
            health=WorkloadHealth(
                namespace="payments",
                name="checkout",
                kind="Deployment",
                desired_replicas=3,
                ready_replicas=1,
                status="Degraded",
                reason="Two replicas are unavailable",
            ),
            pods=(
                PodStatus(
                    namespace="payments",
                    name="checkout-abc",
                    phase="Running",
                    ready=False,
                    restart_count=3,
                    reason="CrashLoopBackOff",
                ),
            ),
            events=(
                KubernetesEvent(
                    namespace="payments",
                    involved_object="checkout-abc",
                    reason="BackOff",
                    message="Back-off restarting failed container",
                    event_type="Warning",
                ),
            ),
            logs=(
                ContainerLog(
                    namespace="payments",
                    pod_name="checkout-abc",
                    container_name="checkout",
                    text="panic: missing PAYMENT_GATEWAY_URL environment variable",
                    previous=True,
                ),
            ),
            recommendations=("Inspect previous container logs.",),
        )


def test_classify_intent_detects_cluster_health() -> None:
    intent = classify_intent("Show unhealthy workloads in the cluster")

    assert intent.name == "cluster_health"
    assert intent.confidence > 0.9


def test_classify_intent_detects_incident_reports_before_diagnosis() -> None:
    intent = classify_intent("Create an incident report for deployment checkout")

    assert intent.name == "incident_report"


def test_classify_intent_defaults_to_runbook_answer() -> None:
    intent = classify_intent("How do we perform a rolling restart?")

    assert intent.name == "runbook_answer"


def test_build_workflow_steps_for_deployment_diagnosis() -> None:
    intent = classify_intent("Diagnose deployment checkout")

    steps = build_workflow_steps(intent)

    assert [step.name for step in steps] == [
        "classify_intent",
        "retrieve_context",
        "diagnose_deployment",
        "synthesize_diagnosis",
        "review_output",
    ]


def test_review_agent_output_rejects_blank_answers() -> None:
    assert review_agent_output(AgentOutput(answer="ok")) is True
    assert review_agent_output(AgentOutput(answer="   ")) is False
    assert review_agent_output(None) is False


@pytest.mark.anyio
async def test_graph_agent_falls_back_to_injected_agent() -> None:
    agent = GraphAgent(fallback_agent=EchoAgent())

    output = await agent.run(AgentInput(message="hello"))

    assert output.answer == "echo: hello"


@pytest.mark.anyio
async def test_graph_agent_routes_cluster_health_branch() -> None:
    agent = GraphAgent(
        fallback_agent=KubePilotAgent(
            retriever=KeywordRetriever(
                [
                    Document(
                        source="unhealthy.md",
                        title="Unhealthy workloads",
                        content="List degraded workloads.",
                    )
                ],
            ),
            cluster_inspector=FakeClusterInspector(),
        )
    )

    output = await agent.run(AgentInput(message="Show unhealthy workloads"))

    assert "payments/deployment/checkout has 1/3 replicas ready" in output.answer
    assert output.sources == ("Unhealthy workloads",)


@pytest.mark.anyio
async def test_graph_agent_routes_incident_report_branch() -> None:
    agent = GraphAgent(
        fallback_agent=KubePilotAgent(
            retriever=KeywordRetriever(
                [
                    Document(
                        source="deployment.md",
                        title="Deployment rollout failures",
                        content="Use pod events and previous logs to diagnose rollouts.",
                    )
                ],
            ),
            cluster_inspector=FakeClusterInspector(),
            deployment_diagnoser=FakeDeploymentDiagnoser(),
        )
    )

    output = await agent.run(
        AgentInput(message="Create an incident report for deployment checkout")
    )

    assert "Deployment incident: payments/deployment/checkout" in output.answer
    assert "Severity: warning" in output.answer
    assert output.sources == ("Deployment rollout failures",)
