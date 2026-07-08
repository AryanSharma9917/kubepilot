"""LLM client interfaces and local provider implementations."""

from typing import Protocol


class LLMClient(Protocol):
    """Completion interface implemented by language model providers."""

    async def complete(self, prompt: str) -> str:
        """Return a model response for a prompt."""


class DeterministicLLMClient:
    """Offline-safe LLM stand-in for tests and local development."""

    async def complete(self, prompt: str) -> str:
        """Create a stable answer from a grounded prompt."""

        context = _section(prompt, "CONTEXT")
        if not context:
            return "No matching runbook was found yet."

        first_context_line = context.splitlines()[0].strip()
        return f"Based on the retrieved runbooks, {first_context_line}"


def _section(prompt: str, name: str) -> str:
    marker = f"{name}:\n"
    start = prompt.find(marker)
    if start == -1:
        return ""
    start += len(marker)
    next_marker = prompt.find("\n\n", start)
    value = prompt[start:] if next_marker == -1 else prompt[start:next_marker]
    return value.strip()
