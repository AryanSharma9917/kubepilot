import pytest

from agent.answers import create_answer_synthesizer
from agent.answers.synthesis import GroundedAnswerSynthesizer
from agent.llm import HTTPJSONLLMClient


@pytest.mark.anyio
async def test_http_json_llm_client_uses_injected_transport() -> None:
    client = HTTPJSONLLMClient(
        "http://llm.local/complete",
        transport=lambda prompt: f"answer for {prompt}",
    )

    answer = await client.complete("question")

    assert answer == "answer for question"


def test_create_answer_synthesizer_requires_http_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KUBEPILOT_LLM_PROVIDER", "http")
    monkeypatch.delenv("KUBEPILOT_LLM_ENDPOINT", raising=False)

    with pytest.raises(ValueError, match="KUBEPILOT_LLM_ENDPOINT"):
        create_answer_synthesizer()


def test_create_answer_synthesizer_supports_http_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KUBEPILOT_LLM_PROVIDER", "http")
    monkeypatch.setenv("KUBEPILOT_LLM_ENDPOINT", "http://llm.local/complete")

    synthesizer = create_answer_synthesizer()

    assert isinstance(synthesizer, GroundedAnswerSynthesizer)
