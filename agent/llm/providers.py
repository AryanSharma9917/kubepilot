"""LLM client interfaces and local provider implementations."""

import asyncio
import json
import urllib.request
from collections.abc import Callable
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


class HTTPJSONLLMClient:
    """LLM client for self-hosted HTTP JSON completion services."""

    def __init__(
        self,
        endpoint: str,
        *,
        timeout_seconds: float = 10.0,
        transport: Callable[[str], str] | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def complete(self, prompt: str) -> str:
        """Return a completion from a self-hosted HTTP JSON service."""

        if self._transport is not None:
            return self._transport(prompt)
        return await asyncio.to_thread(self._complete_sync, prompt)

    def _complete_sync(self, prompt: str) -> str:
        payload = json.dumps({"prompt": prompt}).encode("utf-8")
        request = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            body = response.read().decode("utf-8")
        data = json.loads(body)
        answer = data.get("answer", data.get("text"))
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                "LLM provider response must include a non-empty answer or text field."
            )
        return answer.strip()
