"""Grounded answer synthesis for retrieved runbook context."""

import os
from dataclasses import dataclass
from typing import Protocol

from agent.answers.prompts import build_grounded_answer_prompt, citations_from_matches
from agent.llm import DeterministicLLMClient, LLMClient
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
    raise ValueError(f"Unsupported LLM provider: {provider}")


def _source_titles(matches: list[RetrievedDocument]) -> tuple[str, ...]:
    unique_titles: list[str] = []
    for match in matches:
        title = match.document.title
        if title not in unique_titles:
            unique_titles.append(title)
    return tuple(unique_titles)
