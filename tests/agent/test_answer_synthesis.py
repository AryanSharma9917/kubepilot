import pytest

from agent.answers import GroundedAnswerSynthesizer
from agent.answers.prompts import build_grounded_answer_prompt, citations_from_matches
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

    assert "Based on the retrieved runbooks" in answer.answer
    assert "Check pod events first." in answer.answer
    assert answer.sources == ("Deployment rollout failures",)
    assert answer.citations[0].title == "Deployment rollout failures"
    assert answer.citations[0].source == "deployment.md"


@pytest.mark.anyio
async def test_grounded_answer_synthesizer_handles_missing_context() -> None:
    synthesizer = GroundedAnswerSynthesizer()

    answer = await synthesizer.synthesize(message="What changed?", matches=[])

    assert answer.answer == (
        'KubePilot received your question: "What changed?". '
        "No matching runbook was found yet."
    )
    assert answer.sources == ()


def test_grounded_answer_prompt_includes_question_and_context() -> None:
    prompt = build_grounded_answer_prompt(
        message="How do I restart pods?",
        matches=[
            RetrievedDocument(
                document=Document(
                    source="restart.md",
                    title="Rolling restart",
                    content="Use kubectl rollout restart deployment/api.",
                ),
                score=1.0,
            )
        ],
    )

    assert "QUESTION:\nHow do I restart pods?" in prompt
    assert "[1] Rolling restart: Use kubectl rollout restart deployment/api." in prompt


def test_citations_from_matches_deduplicates_source_titles() -> None:
    matches = [
        RetrievedDocument(
            document=Document(
                source="restart.md",
                title="Rolling restart",
                content="Use kubectl rollout restart deployment/api.",
            ),
            score=2.0,
        ),
        RetrievedDocument(
            document=Document(
                source="restart.md",
                title="Rolling restart",
                content="Watch rollout status after restarting.",
            ),
            score=1.0,
        ),
    ]

    citations = citations_from_matches(matches)

    assert len(citations) == 1
    assert citations[0].snippet == "Use kubectl rollout restart deployment/api."
