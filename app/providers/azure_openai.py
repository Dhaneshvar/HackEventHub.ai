"""Azure OpenAI provider using the standard OpenAI SDK with /openai/v1/ endpoint."""

from __future__ import annotations

import time
from typing import Any

import httpx
from openai import APIConnectionError, APIError, AsyncOpenAI

from app.core.config import settings
from app.providers.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ProviderCapabilities,
)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI via the /openai/v1/ routing endpoint (no api-version needed)."""

    def __init__(
        self,
        base_url: str | None = None,
        deployment: str | None = None,
        api_key: str | None = None,
        use_entra_id: bool | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._base_url = base_url or settings.azure_openai_endpoint
        self._deployment = deployment or settings.azure_openai_deployment
        self._use_entra_id = (
            use_entra_id if use_entra_id is not None else settings.azure_use_entra_id
        )

        if self._use_entra_id:
            resolved_key = self._get_entra_token()
        else:
            resolved_key = api_key or settings.azure_openai_api_key

        client_kwargs: dict[str, Any] = {
            "base_url": self._base_url,
            "api_key": resolved_key or "not-configured",
        }
        if http_client is not None:
            client_kwargs["http_client"] = http_client
        self._client = AsyncOpenAI(**client_kwargs)

    @staticmethod
    def _get_entra_token() -> str:
        """Get a bearer token from Azure Entra ID (Azure AD)."""
        try:
            from azure.identity import (
                DefaultAzureCredential,
                get_bearer_token_provider,
            )

            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            return token_provider()
        except ImportError as err:
            raise RuntimeError(
                "azure-identity is required for Entra ID auth. "
                "Install with: pip install azure-identity"
            ) from err
        except Exception as e:
            raise RuntimeError(f"Entra ID authentication failed: {e}") from e

    def name(self) -> str:
        return "azure"

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            tool_calling=True,
            json_mode=True,
            reasoning_effort=False,
        )

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
        openai_messages = _to_openai_messages(messages)

        kwargs: dict[str, Any] = {
            "model": self._deployment,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if response_format:
            kwargs["response_format"] = response_format

        response = await self._client.chat.completions.create(**kwargs)
        return _parse_response(response)

    async def test_connection(self) -> dict[str, Any]:
        if not self._base_url or not self._deployment:
            return {
                "ok": False,
                "error": "Azure OpenAI endpoint and deployment must be configured",
            }
        start = time.monotonic()
        try:
            await self._client.chat.completions.create(
                model=self._deployment,
                messages=[{"role": "user", "content": "Say 'ok'"}],
                max_tokens=10,
            )
            latency_ms = (time.monotonic() - start) * 1000

            tool_support = True
            try:
                await self._client.chat.completions.create(
                    model=self._deployment,
                    messages=[{"role": "user", "content": "What is 2+2?"}],
                    tools=[
                        {
                            "type": "function",
                            "function": {
                                "name": "test",
                                "description": "Test function",
                                "parameters": {"type": "object", "properties": {}},
                            },
                        }
                    ],
                    max_tokens=10,
                )
            except Exception:
                tool_support = False

            return {
                "ok": True,
                "latency_ms": round(latency_ms, 1),
                "model": self._deployment,
                "tool_calling": tool_support,
                "json_mode": True,
            }
        except APIConnectionError as e:
            return {"ok": False, "error": f"Connection failed: {e}"}
        except APIError as e:
            return {"ok": False, "error": f"API error: {e}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    result = []
    for m in messages:
        msg: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        if m.name:
            msg["name"] = m.name
        if m.tool_calls:
            msg["tool_calls"] = m.tool_calls
        result.append(msg)
    return result


def _parse_response(response) -> ChatResponse:
    choice = response.choices[0]
    tool_calls_out = []
    if choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            tool_calls_out.append(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
            )
    return ChatResponse(
        content=choice.message.content or "",
        tool_calls=tool_calls_out,
        finish_reason=choice.finish_reason or "stop",
        usage={
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        },
        raw=response,
    )
