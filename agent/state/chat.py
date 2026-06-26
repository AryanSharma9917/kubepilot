"""State models for chat-style agent requests."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentInput:
    """Input passed from the API layer into the agent."""

    message: str


@dataclass(frozen=True)
class AgentOutput:
    """Output returned by the agent to the API layer."""

    answer: str
