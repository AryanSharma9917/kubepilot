"""Grounded answer synthesis for retrieved runbook context."""

import os
from dataclasses import dataclass
from typing import Protocol

from agent.answers.prompts import build_grounded_answer_prompt, citations_from_matches
from agent.llm import (
    AzureOpenAILLMClient,
    DeterministicLLMClient,
    HTTPJSONLLMClient,
    LLMClient,
    OpenAICompatibleLLMClient,
)
from agent.state.chat import Citation
from rag import RetrievedDocument


@dataclass(frozen=True)
class GroundedAnswer:
    """Answer text and cited source titles."""

    answer: str
    sources: tuple[str, ...]
    citations: tuple[Citation, ...] = ()


class AnswerSynthesizer(Protocol):
    """Interface for answer synthesis implementations."""

    async def synthesize(
        self,
        *,
        message: str,
        matches: list[RetrievedDocument],
    ) -> GroundedAnswer:
        """Build an answer from a user message and retrieved context."""


class GroundedAnswerSynthesizer:
    """Deterministic answer synthesizer grounded in retrieved runbook chunks."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client or DeterministicLLMClient()

    async def synthesize(
        self,
        *,
        message: str,
        matches: list[RetrievedDocument],
    ) -> GroundedAnswer:
        """Return a concise source-grounded answer."""

        sources = _source_titles(matches)
        base_answer = f'KubePilot received your question: "{message}".'
        if not matches:
            return GroundedAnswer(
                answer=f"{base_answer} No matching runbook was found yet.",
                sources=(),
            )

        prompt = build_grounded_answer_prompt(message=message, matches=matches)
        model_answer = await self._llm_client.complete(prompt)
        citations = citations_from_matches(matches)
        source_list = ", ".join(sources)
        return GroundedAnswer(
            answer=(
                f"{base_answer} {model_answer} Sources: {source_list}."
            ),
            sources=sources,
            citations=citations,
        )


def create_answer_synthesizer() -> AnswerSynthesizer:
    """Create the configured answer synthesizer."""

    provider = os.getenv("KUBEPILOT_LLM_PROVIDER", "deterministic")
    if provider == "deterministic":
        return GroundedAnswerSynthesizer()
    if provider == "http":
        endpoint = os.getenv("KUBEPILOT_LLM_ENDPOINT")
        if not endpoint:
            raise ValueError("KUBEPILOT_LLM_ENDPOINT is required when KUBEPILOT_LLM_PROVIDER=http")
        return GroundedAnswerSynthesizer(HTTPJSONLLMClient(endpoint))
    if provider == "openai":
        api_key = os.getenv("KUBEPILOT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("KUBEPILOT_LLM_MODEL")
        if not api_key or not model:
            missing = []
            if not api_key:
                missing.append("KUBEPILOT_LLM_API_KEY")
            if not model:
                missing.append("KUBEPILOT_LLM_MODEL")
            raise ValueError(
                "KUBEPILOT_LLM_API_KEY and KUBEPILOT_LLM_MODEL are required when "
                f"KUBEPILOT_LLM_PROVIDER=openai. Missing: {', '.join(missing)}"
            )
        endpoint = (
            os.getenv("KUBEPILOT_LLM_ENDPOINT")
            or "https://api.openai.com/v1/chat/completions"
        )
        return GroundedAnswerSynthesizer(
            OpenAICompatibleLLMClient(api_key, model, endpoint=endpoint)
        )
    if provider == "azure_openai":
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        missing = []
        if not api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if not endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not deployment:
            missing.append("AZURE_OPENAI_DEPLOYMENT")
        if missing:
            raise ValueError(
                "Azure OpenAI configuration is incomplete. Missing: "
                + ", ".join(missing)
            )
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        return GroundedAnswerSynthesizer(
            AzureOpenAILLMClient(
                api_key,
                endpoint,
                deployment,
                api_version=api_version,
            )
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")


def _source_titles(matches: list[RetrievedDocument]) -> tuple[str, ...]:
    unique_titles: list[str] = []
    for match in matches:
        title = match.document.title
        if title not in unique_titles:
            unique_titles.append(title)
    return tuple(unique_titles)
