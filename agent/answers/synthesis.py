"""Grounded answer synthesis for retrieved runbook context."""

from dataclasses import dataclass
from typing import Protocol

from rag import RetrievedDocument


@dataclass(frozen=True)
class GroundedAnswer:
    """Answer text and cited source titles."""

    answer: str
    sources: tuple[str, ...]


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

        evidence = " ".join(_context_sentence(match) for match in matches[:2])
        source_list = ", ".join(sources)
        return GroundedAnswer(
            answer=(
                f"{base_answer} Based on {source_list}: "
                f"{evidence} Sources: {source_list}."
            ),
            sources=sources,
        )


def _source_titles(matches: list[RetrievedDocument]) -> tuple[str, ...]:
    unique_titles: list[str] = []
    for match in matches:
        title = match.document.title
        if title not in unique_titles:
            unique_titles.append(title)
    return tuple(unique_titles)


def _context_sentence(match: RetrievedDocument) -> str:
    content = " ".join(match.document.content.split())
    first_sentence = content.split(". ", maxsplit=1)[0].strip()
    if first_sentence and not first_sentence.endswith("."):
        first_sentence = f"{first_sentence}."
    return first_sentence or match.document.title
