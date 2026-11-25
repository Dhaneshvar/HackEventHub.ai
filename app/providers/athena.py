"""Unisys Athena EA provider -- SKELETON.

TODO: This is a placeholder. The actual API contract will be provided by the user.
If Athena turns out to be OpenAI-compatible, this adapter can delegate to the
OpenAI SDK with custom base_url and auth. Otherwise, implement from the docs.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.providers.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ProviderCapabilities,
)


class AthenaProvider(LLMProvider):
    """Unisys Athena EA -- skeleton adapter.

    TODO: Replace with actual implementation once API docs are provided.
    Currently configured via env vars:
    - ATHENA_BASE_URL
    - ATHENA_API_KEY
    - ATHENA_MODEL
    - ATHENA_AUTH_HEADER
    - ATHENA_AUTH_SCHEME
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self._base_url = base_url or settings.athena_base_url
        self._api_key = api_key or settings.athena_api_key
        self._model = model or settings.athena_model
        self._auth_header = settings.athena_auth_header
        self._auth_scheme = settings.athena_auth_scheme

    def name(self) -> str:
        return "athena"

    def capabilities(self) -> ProviderCapabilities:
        # TODO: Update once API contract is known
        return ProviderCapabilities(
            tool_calling=False,
            json_mode=False,
            reasoning_effort=False,
        )

    def _auth_headers(self) -> dict[str, str]:
        if self._api_key:
            return {self._auth_header: f"{self._auth_scheme} {self._api_key}"}
        return {}

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
        if not self._base_url:
            raise RuntimeError("Athena is not configured: ATHENA_BASE_URL is empty")

        # TODO: Replace with actual API call structure once docs are provided.
        # Assuming OpenAI-compatible format as default.
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self._base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers={
                    **self._auth_headers(),
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        # TODO: Parse according to actual response format
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})

        return ChatResponse(
            content=message.get("content", ""),
            tool_calls=[],  # TODO: Parse tool calls if supported
            finish_reason=choice.get("finish_reason", "stop"),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            raw=data,
        )

    async def test_connection(self) -> dict[str, Any]:
        if not self._base_url:
            return {
                "ok": False,
                "error": "Athena is not configured: set ATHENA_BASE_URL and ATHENA_API_KEY",
                "note": "TODO: Awaiting API documentation from user",
            }
        start = time.monotonic()
        try:
            await self.chat(
                [ChatMessage(role="user", content="Say 'ok'")],
                max_tokens=10,
            )
            latency_ms = (time.monotonic() - start) * 1000
            return {
                "ok": True,
                "latency_ms": round(latency_ms, 1),
                "model": self._model,
                "tool_calling": False,
                "json_mode": False,
                "note": "TODO: Capabilities TBD pending API docs",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
