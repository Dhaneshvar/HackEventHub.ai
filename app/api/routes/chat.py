"""Agent Chat Playground API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import verify_dashboard_token
from app.providers.base import ChatMessage
from app.providers.router import llm_router

router = APIRouter(dependencies=[Depends(verify_dashboard_token)])


class ChatMessageRequest(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessageRequest]
    provider: str | None = None


@router.post("")
async def playground_chat(body: ChatRequest):
    """Playground chat with the agent and inspect tool calls."""
    messages = [ChatMessage(role=m.role, content=m.content) for m in body.messages]
    target_provider = body.provider or llm_router.get_active()

    try:
        provider = llm_router.get_provider(target_provider)
        response = await provider.chat(
            messages,
            task="chat",
            temperature=0.3,
        )
        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": response.tool_calls,
            "finish_reason": response.finish_reason,
            "provider": target_provider,
            "usage": response.usage,
        }
    except Exception as e:
        return {
            "role": "assistant",
            "content": f"Error from provider '{target_provider}': {e}",
            "tool_calls": [],
            "finish_reason": "error",
            "provider": target_provider,
        }
