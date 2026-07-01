import pytest

from agent import AgentInput, KubePilotAgent
from agent.tools.kubernetes import ClusterHealth, WorkloadHealth
from rag.models import Document
from rag.retrieval import KeywordRetriever


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


@pytest.mark.anyio
async def test_agent_returns_runbook_sources_when_available() -> None:
    agent = KubePilotAgent(
        retriever=KeywordRetriever(
            [
                Document(
                    source="deployment.md",
                    title="Deployment rollout failures",
                    content="ImagePullBackOff and rollout failures.",
                )
            ],
        ),
        cluster_inspector=FakeClusterInspector(),
    )

    output = await agent.run(AgentInput(message="Why is my deployment failing?"))

    assert output.answer == (
        'KubePilot received your question: "Why is my deployment failing?". '
        "Relevant runbooks: Deployment rollout failures."
    )
    assert output.sources == ("Deployment rollout failures",)


@pytest.mark.anyio
async def test_agent_handles_missing_runbook_context() -> None:
    agent = KubePilotAgent(
        retriever=KeywordRetriever([]),
        cluster_inspector=FakeClusterInspector(),
    )

    output = await agent.run(AgentInput(message="What is happening?"))

    assert output.answer == (
        'KubePilot received your question: "What is happening?". '
        "No matching runbook was found yet."
    )
    assert output.sources == ()


@pytest.mark.anyio
async def test_agent_uses_cluster_tool_for_unhealthy_workload_questions() -> None:
    agent = KubePilotAgent(
        retriever=KeywordRetriever(
            [
                Document(
                    source="unhealthy-workloads.md",
                    title="Unhealthy workloads",
                    content="List Deployments with unavailable replicas.",
                )
            ],
        ),
        cluster_inspector=FakeClusterInspector(),
    )

    output = await agent.run(AgentInput(message="Show unhealthy workloads"))

    assert output.answer == (
        'KubePilot received your question: "Show unhealthy workloads". '
        "Unhealthy workloads: payments/deployment/checkout has 1/3 replicas "
        "ready (Two replicas are unavailable)."
    )
    assert output.sources == ("Unhealthy workloads",)
