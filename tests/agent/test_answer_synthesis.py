import pytest

from agent.answers import GroundedAnswerSynthesizer
from rag.models import Document, RetrievedDocument


@pytest.mark.anyio
async def test_grounded_answer_synthesizer_uses_retrieved_context() -> None:
    synthesizer = GroundedAnswerSynthesizer()

    answer = await synthesizer.synthesize(
        message="How do I fix rollout failures?",
        matches=[
            RetrievedDocument(
                document=Document(
                    source="deployment.md",
                    title="Deployment rollout failures",
                    content="Check pod events first. Then inspect image pull errors.",
                ),
                score=2.0,
            )
        ],
    )

    assert "Based on Deployment rollout failures" in answer.answer
    assert "Check pod events first." in answer.answer
    assert answer.sources == ("Deployment rollout failures",)


@pytest.mark.anyio
async def test_grounded_answer_synthesizer_handles_missing_context() -> None:
    synthesizer = GroundedAnswerSynthesizer()

    answer = await synthesizer.synthesize(message="What changed?", matches=[])

    assert answer.answer == (
        'KubePilot received your question: "What changed?". '
        "No matching runbook was found yet."
    )
    assert answer.sources == ()
