"""Provider management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import verify_dashboard_token
from app.core.config import settings
from app.db.models import ProviderConfig, utc_now
from app.db.session import get_session
from app.providers.router import llm_router

router = APIRouter(dependencies=[Depends(verify_dashboard_token)])


class ProviderConfigUpdate(BaseModel):
    base_url: str | None = None
    model_name: str | None = None
    task_profiling: str | None = None
    task_extraction: str | None = None
    task_relevance: str | None = None
    task_chat: str | None = None


class SetActiveRequest(BaseModel):
    provider: str


@router.get("")
async def list_providers(session: AsyncSession = Depends(get_session)):
    """List all providers with their config and status."""
    result = await session.execute(select(ProviderConfig))
    configs = result.scalars().all()

    runtime = llm_router.list_providers()
    providers_list = []
    for cfg in configs:
        rt = runtime.get(cfg.name, {})
        providers_list.append(
            {
                "name": cfg.name,
                "is_active": cfg.is_active,
                "base_url": cfg.base_url,
                "model_name": cfg.model_name,
                "has_api_key": cfg.has_api_key or _has_key(cfg.name),
                "supports_tool_calling": cfg.supports_tool_calling,
                "supports_json_mode": cfg.supports_json_mode,
                "last_test_at": cfg.last_test_at.isoformat() if cfg.last_test_at else None,
                "last_test_latency_ms": cfg.last_test_latency_ms,
                "last_test_error": cfg.last_test_error,
                "capabilities": rt.get("capabilities", {}),
                "task_profiling": cfg.task_profiling,
                "task_extraction": cfg.task_extraction,
                "task_relevance": cfg.task_relevance,
                "task_chat": cfg.task_chat,
            }
        )
    return {"providers": providers_list}


def _has_key(name: str) -> bool:
    """Check if the provider has an API key configured in env."""
    if name == "ollama":
        return True  # No key needed
    if name == "azure":
        return bool(settings.azure_openai_api_key) or settings.azure_use_entra_id
    if name == "athena":
        return bool(settings.athena_api_key)
    return False


@router.put("/active")
async def set_active_provider(
    req: SetActiveRequest,
    session: AsyncSession = Depends(get_session),
):
    """Switch the active LLM provider."""
    valid_names = {"ollama", "azure", "athena"}
    if req.provider not in valid_names:
        raise HTTPException(400, f"Unknown provider: {req.provider}")

    try:
        llm_router.set_active(req.provider)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    # Update DB
    result = await session.execute(select(ProviderConfig))
    for cfg in result.scalars().all():
        cfg.is_active = cfg.name == req.provider
        session.add(cfg)
    await session.commit()

    return {"active": req.provider}


@router.post("/{name}/test")
async def test_provider(
    name: str,
    session: AsyncSession = Depends(get_session),
):
    """Test a provider connection."""
    try:
        provider = llm_router.get_provider(name)
    except ValueError as err:
        raise HTTPException(404, f"Unknown provider: {name}") from err

    result = await provider.test_connection()

    # Update DB record
    db_result = await session.execute(select(ProviderConfig).where(ProviderConfig.name == name))
    cfg = db_result.scalars().first()
    if cfg:
        cfg.last_test_at = utc_now()
        cfg.last_test_latency_ms = result.get("latency_ms")
        cfg.last_test_error = result.get("error", "")
        cfg.supports_tool_calling = result.get("tool_calling")
        cfg.supports_json_mode = result.get("json_mode")
        cfg.has_api_key = _has_key(name)
        session.add(cfg)
        await session.commit()

    return result


@router.put("/{name}/config")
async def update_provider_config(
    name: str,
    update: ProviderConfigUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update non-secret provider settings."""
    result = await session.execute(select(ProviderConfig).where(ProviderConfig.name == name))
    cfg = result.scalars().first()
    if not cfg:
        raise HTTPException(404, f"Unknown provider: {name}")

    if update.base_url is not None:
        cfg.base_url = update.base_url
    if update.model_name is not None:
        cfg.model_name = update.model_name
    if update.task_profiling is not None:
        cfg.task_profiling = update.task_profiling
    if update.task_extraction is not None:
        cfg.task_extraction = update.task_extraction
    if update.task_relevance is not None:
        cfg.task_relevance = update.task_relevance
    if update.task_chat is not None:
        cfg.task_chat = update.task_chat

    session.add(cfg)
    await session.commit()
    return {"ok": True}
