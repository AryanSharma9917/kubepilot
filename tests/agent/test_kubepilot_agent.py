import pytest

from agent import AgentInput, KubePilotAgent
from rag.models import Document
from rag.retrieval import KeywordRetriever


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
    )

    output = await agent.run(AgentInput(message="Why is my deployment failing?"))

    assert output.answer == (
        'KubePilot received your question: "Why is my deployment failing?". '
        "Relevant runbooks: Deployment rollout failures."
    )
    assert output.sources == ("Deployment rollout failures",)


@pytest.mark.anyio
async def test_agent_handles_missing_runbook_context() -> None:
    agent = KubePilotAgent(retriever=KeywordRetriever([]))

    output = await agent.run(AgentInput(message="What is happening?"))

    assert output.answer == (
        'KubePilot received your question: "What is happening?". '
        "No matching runbook was found yet."
    )
    assert output.sources == ()
