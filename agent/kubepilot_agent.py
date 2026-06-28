"""Initial KubePilot agent boundary."""

from typing import Protocol

from agent.state.chat import AgentInput, AgentOutput
from rag import KeywordRetriever, RetrievedDocument, create_default_retriever


class Agent(Protocol):
    """Interface implemented by KubePilot agent runtimes."""

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Run the agent for a single user message."""


class KubePilotAgent:
    """Deterministic agent shell that can retrieve local runbook context."""

    def __init__(self, retriever: KeywordRetriever | None = None) -> None:
        self._retriever = retriever or create_default_retriever()

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Return a stable response grounded in matching runbooks when possible."""

        matches = self._retriever.search(agent_input.message)
        sources = _source_titles(matches)

        return AgentOutput(
            answer=_build_answer(agent_input.message, sources),
            sources=sources,
        )


def create_agent() -> Agent:
    """Create the default KubePilot agent runtime."""

    return KubePilotAgent()


def _source_titles(matches: list[RetrievedDocument]) -> tuple[str, ...]:
    unique_titles: list[str] = []
    for match in matches:
        title = match.document.title
        if title not in unique_titles:
            unique_titles.append(title)
    return tuple(unique_titles)


def _build_answer(message: str, sources: tuple[str, ...]) -> str:
    base_answer = f'KubePilot received your question: "{message}".'

    if not sources:
        return f"{base_answer} No matching runbook was found yet."

    source_list = ", ".join(sources)
    return f"{base_answer} Relevant runbooks: {source_list}."
