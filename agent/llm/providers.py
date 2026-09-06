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


class OpenAICompatibleLLMClient:
    """LLM client for OpenAI-compatible REST APIs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        endpoint: str = "https://api.openai.com/v1/chat/completions",
        timeout_seconds: float = 30.0,
        transport: Callable[[str], str] | None = None,
        api_version: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._api_version = api_version

    async def complete(self, prompt: str) -> str:
        """Return a completion from an OpenAI-compatible API."""

        if self._transport is not None:
            return self._transport(prompt)
        return await asyncio.to_thread(self._complete_sync, prompt)

    def _complete_sync(self, prompt: str) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 250,
        }
        raw_body = json.dumps(payload).encode("utf-8")
        headers = {
            "content-type": "application/json",
            "api-key": self._api_key,
        }
        endpoint = self._endpoint
        if self._api_version:
            separator = "&" if "?" in endpoint else "?"
            endpoint = f"{endpoint}{separator}api-version={self._api_version}"
        request = urllib.request.Request(
            endpoint,
            data=raw_body,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            body = response.read().decode("utf-8")
        data = json.loads(body)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("OpenAI-compatible LLM response did not include any choices.")
        message = choices[0].get("message") or {}
        answer = message.get("content") or choices[0].get("text")
        if isinstance(answer, list):
            answer = "".join(part.get("text", "") for part in answer if isinstance(part, dict))
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                "OpenAI-compatible LLM response must include a non-empty message.content field."
            )
        return answer.strip()


class AzureOpenAILLMClient(OpenAICompatibleLLMClient):
    """LLM client for Azure OpenAI chat completions using deployment names."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment: str,
        *,
        api_version: str = "2024-02-01",
        timeout_seconds: float = 30.0,
        transport: Callable[[str], str] | None = None,
    ) -> None:
        super().__init__(
            api_key,
            deployment,
            endpoint=f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions",
            timeout_seconds=timeout_seconds,
            transport=transport,
            api_version=api_version,
        )
