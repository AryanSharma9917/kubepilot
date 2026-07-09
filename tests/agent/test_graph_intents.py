import pytest

from agent.graph import classify_intent
from agent.graph.workflow import GraphAgent, build_workflow_steps
from agent.state.chat import AgentInput, AgentOutput


class EchoAgent:
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(answer=f"echo: {agent_input.message}", sources=())


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
    ]


@pytest.mark.anyio
async def test_graph_agent_falls_back_to_injected_agent() -> None:
    agent = GraphAgent(fallback_agent=EchoAgent())

    output = await agent.run(AgentInput(message="hello"))

    assert output.answer == "echo: hello"
