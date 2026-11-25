"""LLM Router: routes requests to the active provider with fallback."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.providers.athena import AthenaProvider
from app.providers.azure_openai import AzureOpenAIProvider
from app.providers.base import ChatMessage, ChatResponse, LLMProvider
from app.providers.ollama import OllamaProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes LLM calls to the active provider, with fallback chain."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._active: str = ""
        self._fallback_order: list[str] = []
        self._task_routing: dict[str, str] = {}

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.name()] = provider

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise ValueError(f"Unknown provider: {name}")
        self._active = name

    def set_fallback_order(self, order: list[str]) -> None:
        self._fallback_order = [n for n in order if n in self._providers]

    def set_task_routing(self, routing: dict[str, str]) -> None:
        """Set per-task provider routing."""
        self._task_routing = routing

    def get_active(self) -> str:
        return self._active

    def get_provider(self, name: str | None = None) -> LLMProvider:
        target = name or self._active
        if target not in self._providers:
            raise ValueError(f"Provider '{target}' not registered")
        return self._providers[target]

    def get_provider_for_task(self, task: str) -> LLMProvider:
        """Get the provider for a specific task, falling back to active."""
        name = self._task_routing.get(task, self._active)
        return self.get_provider(name)

    def list_providers(self) -> dict[str, dict[str, Any]]:
        result = {}
        for name, provider in self._providers.items():
            caps = provider.capabilities()
            result[name] = {
                "name": name,
                "is_active": name == self._active,
                "capabilities": {
                    "tool_calling": caps.tool_calling,
                    "json_mode": caps.json_mode,
                    "reasoning_effort": caps.reasoning_effort,
                },
            }
        return result

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        tools: list[dict] | None = None,
        response_format: dict | None = None,
        task: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> ChatResponse:
        """Send chat with automatic fallback on failure."""
        chain: list[str] = []
        if task and task in self._task_routing:
            chain.append(self._task_routing[task])
        if self._active and self._active not in chain:
            chain.append(self._active)
        for fb in self._fallback_order:
            if fb not in chain:
                chain.append(fb)

        last_error: Exception | None = None
        for provider_name in chain:
            provider = self._providers.get(provider_name)
            if not provider:
                continue
            try:
                start = time.monotonic()
                result = await provider.chat(
                    messages,
                    tools=tools,
                    response_format=response_format,
                    task=task,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "LLM call ok: provider=%s task=%s latency=%.0fms",
                    provider_name,
                    task,
                    latency_ms,
                )
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    "LLM call failed: provider=%s task=%s error=%s",
                    provider_name,
                    task,
                    e,
                )
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def test_all(self) -> dict[str, dict[str, Any]]:
        results = {}
        for name, provider in self._providers.items():
            results[name] = await provider.test_connection()
        return results


# Global router instance
llm_router = LLMRouter()


def init_providers() -> None:
    """Initialize and register all configured providers."""
    llm_router.register(OllamaProvider())
    llm_router.register(AzureOpenAIProvider())
    llm_router.register(AthenaProvider())
    llm_router.set_active("ollama")
