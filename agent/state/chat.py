"""State models for chat-style agent requests."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    """A source citation supporting an agent answer."""

    title: str
    source: str
    snippet: str


@dataclass(frozen=True)
class AgentInput:
    """Input passed from the API layer into the agent."""

    message: str


@dataclass(frozen=True)
class AgentOutput:
    """Output returned by the agent to the API layer."""

    answer: str
    sources: tuple[str, ...] = ()
    citations: tuple[Citation, ...] = ()
