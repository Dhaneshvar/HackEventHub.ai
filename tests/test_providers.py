"""Tests for the LLM provider interface and router."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.providers.athena import AthenaProvider
from app.providers.azure_openai import AzureOpenAIProvider
from app.providers.base import ChatMessage, ChatResponse, ProviderCapabilities
from app.providers.ollama import OllamaProvider
from app.providers.router import LLMRouter

# ─── Provider interface tests ──────────────────────────────────────


class TestOllamaProvider:
    def test_name(self):
        provider = OllamaProvider(base_url="http://localhost:11434/v1", model="test")
        assert provider.name() == "ollama"

    def test_capabilities(self):
        provider = OllamaProvider(base_url="http://localhost:11434/v1", model="test")
        caps = provider.capabilities()
        assert isinstance(caps, ProviderCapabilities)
        assert caps.tool_calling is True
        assert caps.json_mode is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_chat_simple(self):
        """Test chat completion with mocked OpenAI-compatible response."""
        respx.post("http://mock-ollama:11434/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "chatcmpl-123",
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "Hello!",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                },
            )
        )

        async with httpx.AsyncClient() as http_client:
            provider = OllamaProvider(
                base_url="http://mock-ollama:11434/v1",
                model="test-model",
                http_client=http_client,
            )
            result = await provider.chat(
                [ChatMessage(role="user", content="Hi")],
            )
            assert isinstance(result, ChatResponse)
            assert result.content == "Hello!"
            assert result.finish_reason == "stop"
            assert result.usage["prompt_tokens"] == 10

    @pytest.mark.asyncio
    @respx.mock
    async def test_chat_with_tool_calls(self):
        """Test that tool calls are parsed correctly."""
        respx.post("http://mock-ollama:11434/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "chatcmpl-456",
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "search_items",
                                            "arguments": '{"query": "hackathon"}',
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
                },
            )
        )

        async with httpx.AsyncClient() as http_client:
            provider = OllamaProvider(
                base_url="http://mock-ollama:11434/v1",
                model="test",
                http_client=http_client,
            )
            result = await provider.chat(
                [ChatMessage(role="user", content="Find hackathons")],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "search_items",
                            "description": "Search items",
                            "parameters": {
                                "type": "object",
                                "properties": {"query": {"type": "string"}},
                            },
                        },
                    }
                ],
            )
            assert len(result.tool_calls) == 1
            assert result.tool_calls[0]["function"]["name"] == "search_items"
            assert result.finish_reason == "tool_calls"

    @pytest.mark.asyncio
    @respx.mock
    async def test_test_connection_success(self):
        """Test connection test with successful response."""
        respx.post("http://mock-ollama:11434/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "chatcmpl-789",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "ok"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
                },
            )
        )
        async with httpx.AsyncClient() as http_client:
            provider = OllamaProvider(
                base_url="http://mock-ollama:11434/v1",
                model="test",
                http_client=http_client,
            )
            result = await provider.test_connection()
            assert result["ok"] is True
            assert "latency_ms" in result
            assert result["model"] == "test"

    @pytest.mark.asyncio
    @respx.mock
    async def test_test_connection_failure(self):
        """Test connection test with failed response."""
        respx.post("http://mock-ollama:11434/v1/chat/completions").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        async with httpx.AsyncClient() as http_client:
            provider = OllamaProvider(
                base_url="http://mock-ollama:11434/v1",
                model="test",
                http_client=http_client,
            )
            result = await provider.test_connection()
            assert result["ok"] is False
            assert "error" in result


class TestAzureOpenAIProvider:
    def test_name(self):
        provider = AzureOpenAIProvider(
            base_url="https://test.openai.azure.com/openai/v1/",
            deployment="test-deploy",
            api_key="test-key",
            use_entra_id=False,
        )
        assert provider.name() == "azure"

    def test_capabilities(self):
        provider = AzureOpenAIProvider(
            base_url="https://test.openai.azure.com/openai/v1/",
            deployment="test-deploy",
            api_key="test-key",
            use_entra_id=False,
        )
        caps = provider.capabilities()
        assert caps.tool_calling is True
        assert caps.json_mode is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_chat_simple(self):
        """Test Azure chat with mocked response."""
        respx.post("https://test.openai.azure.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "chatcmpl-azure",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "Hello from Azure!"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
                },
            )
        )

        async with httpx.AsyncClient() as http_client:
            provider = AzureOpenAIProvider(
                base_url="https://test.openai.azure.com/openai/v1/",
                deployment="gpt-4o",
                api_key="test-key",
                use_entra_id=False,
                http_client=http_client,
            )
            result = await provider.chat([ChatMessage(role="user", content="Hi")])
            assert result.content == "Hello from Azure!"

    @pytest.mark.asyncio
    async def test_test_connection_unconfigured(self):
        """Test connection test when not configured."""
        provider = AzureOpenAIProvider(
            base_url="",
            deployment="",
            api_key="",
            use_entra_id=False,
        )
        result = await provider.test_connection()
        assert result["ok"] is False


class TestAthenaProvider:
    def test_name(self):
        provider = AthenaProvider(base_url="", api_key="", model="")
        assert provider.name() == "athena"

    def test_capabilities_not_yet_known(self):
        provider = AthenaProvider()
        caps = provider.capabilities()
        assert caps.tool_calling is False  # TODO until API docs provided

    @pytest.mark.asyncio
    async def test_chat_unconfigured_raises(self):
        """Chat fails gracefully when not configured."""
        provider = AthenaProvider(base_url="", api_key="")
        with pytest.raises(RuntimeError, match="not configured"):
            await provider.chat([ChatMessage(role="user", content="Hi")])

    @pytest.mark.asyncio
    async def test_test_connection_unconfigured(self):
        provider = AthenaProvider(base_url="", api_key="")
        result = await provider.test_connection()
        assert result["ok"] is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_chat_with_mock_server(self):
        """Test Athena chat against a mocked endpoint."""
        respx.post("https://athena-mock.example.com/api/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {"content": "Athena says hello"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                },
            )
        )
        provider = AthenaProvider(
            base_url="https://athena-mock.example.com/api",
            api_key="test-key",
            model="test",
        )
        result = await provider.chat([ChatMessage(role="user", content="Hi")])
        assert result.content == "Athena says hello"


# ─── Router tests ──────────────────────────────────────────────────


class TestLLMRouter:
    def _make_router(self, http_client: httpx.AsyncClient | None = None) -> LLMRouter:
        router = LLMRouter()
        router.register(
            OllamaProvider(
                base_url="http://mock:11434/v1",
                model="test",
                http_client=http_client,
            )
        )
        router.register(
            AzureOpenAIProvider(
                base_url="https://mock.openai.azure.com/openai/v1/",
                deployment="test",
                api_key="key",
                use_entra_id=False,
                http_client=http_client,
            )
        )
        router.register(AthenaProvider(base_url="", api_key=""))
        router.set_active("ollama")
        return router

    def test_set_active(self):
        router = self._make_router()
        assert router.get_active() == "ollama"
        router.set_active("azure")
        assert router.get_active() == "azure"

    def test_set_active_unknown_raises(self):
        router = self._make_router()
        with pytest.raises(ValueError, match="Unknown provider"):
            router.set_active("nonexistent")

    def test_list_providers(self):
        router = self._make_router()
        providers = router.list_providers()
        assert "ollama" in providers
        assert "azure" in providers
        assert "athena" in providers
        assert providers["ollama"]["is_active"] is True
        assert providers["azure"]["is_active"] is False

    def test_get_provider(self):
        router = self._make_router()
        p = router.get_provider("ollama")
        assert p.name() == "ollama"

    def test_get_provider_for_task_with_routing(self):
        router = self._make_router()
        router.set_task_routing({"profiling": "azure", "chat": "ollama"})
        p = router.get_provider_for_task("profiling")
        assert p.name() == "azure"
        p = router.get_provider_for_task("chat")
        assert p.name() == "ollama"
        # Unrouted task falls back to active
        p = router.get_provider_for_task("extraction")
        assert p.name() == "ollama"

    def test_fallback_order(self):
        router = self._make_router()
        router.set_fallback_order(["azure", "athena"])
        assert router._fallback_order == ["azure", "athena"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_chat_with_fallback(self):
        """When active provider fails, fallback to next."""
        # Ollama fails
        respx.post("http://mock:11434/v1/chat/completions").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        # Azure succeeds
        respx.post("https://mock.openai.azure.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "fallback",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "Fallback worked!"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
                },
            )
        )

        async with httpx.AsyncClient() as http_client:
            router = self._make_router(http_client=http_client)
            router.set_active("ollama")
            router.set_fallback_order(["azure"])

            result = await router.chat([ChatMessage(role="user", content="Hi")])
            assert result.content == "Fallback worked!"

    @pytest.mark.asyncio
    @respx.mock
    async def test_all_providers_fail(self):
        """When all providers fail, raise RuntimeError."""
        respx.post("http://mock:11434/v1/chat/completions").mock(
            side_effect=httpx.ConnectError("fail")
        )
        respx.post("https://mock.openai.azure.com/openai/v1/chat/completions").mock(
            side_effect=httpx.ConnectError("fail")
        )

        async with httpx.AsyncClient() as http_client:
            router = self._make_router(http_client=http_client)
            router.set_active("ollama")
            router.set_fallback_order(["azure"])

            with pytest.raises(RuntimeError, match="All LLM providers failed"):
                await router.chat([ChatMessage(role="user", content="Hi")])

    def test_switching_active_takes_effect_immediately(self):
        """Switching active provider changes next request's target."""
        router = self._make_router()
        assert router.get_active() == "ollama"
        router.set_active("azure")
        p = router.get_provider()
        assert p.name() == "azure"
