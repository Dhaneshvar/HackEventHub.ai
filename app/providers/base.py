"""Abstract LLM provider interface."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderCapabilities:
    tool_calling: bool = False
    json_mode: bool = False
    reasoning_effort: bool = False


@dataclass
class ChatMessage:
    role: str
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ChatResponse:
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class LLMProvider(abc.ABC):
    """Abstract base for all LLM providers."""

    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
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
        """Send a chat completion request."""
        ...

    @abc.abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...

    @abc.abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Test the connection and return latency + capabilities."""
        ...
