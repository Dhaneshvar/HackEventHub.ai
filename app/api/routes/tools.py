"""Tool (website) management API routes -- Phase 1 skeleton."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.api.deps import verify_dashboard_token
from app.db.models import DomainType, FetchMethod, Tool, ToolKind, ToolStatus, utc_now
from app.db.session import get_session

router = APIRouter(dependencies=[Depends(verify_dashboard_token)])


class ToolCreate(BaseModel):
    url: str
    note: str = ""
    domain: DomainType = DomainType.EVENTS


class ToolUpdate(BaseModel):
    name: str | None = None
    kind: ToolKind | None = None
    domain: DomainType | None = None
    description: str | None = None
    fetch_method: FetchMethod | None = None
    listing_urls: list[str] | None = None
    crawl_interval_minutes: int | None = None
    enabled: bool | None = None
    agent_visible: bool | None = None
    user_note: str | None = None


class BulkImport(BaseModel):
    tools: list[ToolCreate]


@router.get("")
async def list_tools(session: AsyncSession = Depends(get_session)):
    """List all registered tools."""
    result = await session.execute(select(Tool).order_by(col(Tool.created_at).desc()))
    tools = result.scalars().all()
    return {"tools": [_tool_to_dict(t) for t in tools]}


@router.post("")
async def create_tool(
    body: ToolCreate,
    session: AsyncSession = Depends(get_session),
):
    """Register a new tool (website). Creates a DRAFT for profiling."""
    # Check for duplicate
    existing = await session.execute(select(Tool).where(Tool.url == body.url))
    if existing.scalars().first():
        raise HTTPException(409, "Tool with this URL already exists")

    tool = Tool(
        url=body.url,
        user_note=body.note,
        domain=body.domain,
        status=ToolStatus.DRAFT,
    )
    session.add(tool)
    await session.commit()
    await session.refresh(tool)

    # TODO (Phase 2): trigger auto-profiling background job

    return _tool_to_dict(tool)


@router.get("/{tool_id}")
async def get_tool(tool_id: int, session: AsyncSession = Depends(get_session)):
    """Get a single tool by ID."""
    tool = await session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(404, "Tool not found")
    return _tool_to_dict(tool)


@router.put("/{tool_id}")
async def update_tool(
    tool_id: int,
    body: ToolUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update tool fields. Used for confirming a profile or changing settings."""
    tool = await session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(404, "Tool not found")

    for field_name, value in body.model_dump(exclude_unset=True).items():
        setattr(tool, field_name, value)

    tool.updated_at = utc_now()
    session.add(tool)
    await session.commit()
    await session.refresh(tool)
    return _tool_to_dict(tool)


@router.post("/{tool_id}/confirm")
async def confirm_tool(tool_id: int, session: AsyncSession = Depends(get_session)):
    """Confirm a draft tool, enabling it for crawling."""
    tool = await session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(404, "Tool not found")
    tool.status = ToolStatus.ACTIVE
    tool.enabled = True
    tool.updated_at = utc_now()
    session.add(tool)
    await session.commit()
    return _tool_to_dict(tool)


@router.delete("/{tool_id}")
async def delete_tool(tool_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a tool."""
    tool = await session.get(Tool, tool_id)
    if not tool:
        raise HTTPException(404, "Tool not found")
    await session.delete(tool)
    await session.commit()
    return {"ok": True}


@router.post("/bulk-import")
async def bulk_import_tools(
    body: BulkImport,
    session: AsyncSession = Depends(get_session),
):
    """Bulk import tools from a list. Each becomes a DRAFT."""
    created = []
    skipped = []
    for item in body.tools:
        existing = await session.execute(select(Tool).where(Tool.url == item.url))
        if existing.scalars().first():
            skipped.append(item.url)
            continue
        tool = Tool(
            url=item.url,
            user_note=item.note,
            domain=item.domain,
            status=ToolStatus.DRAFT,
        )
        session.add(tool)
        await session.flush()
        created.append(_tool_to_dict(tool))

    await session.commit()
    return {"created": created, "skipped": skipped}


def _tool_to_dict(tool: Tool) -> dict[str, Any]:
    return {
        "id": tool.id,
        "url": tool.url,
        "name": tool.name,
        "kind": tool.kind.value if tool.kind else None,
        "domain": tool.domain.value if tool.domain else None,
        "description": tool.description,
        "fetch_method": tool.fetch_method.value if tool.fetch_method else None,
        "listing_urls": tool.listing_urls or [],
        "needs_js": tool.needs_js,
        "crawl_interval_minutes": tool.crawl_interval_minutes,
        "enabled": tool.enabled,
        "agent_visible": tool.agent_visible,
        "is_preset": tool.is_preset,
        "user_note": tool.user_note,
        "profile_confidence": tool.profile_confidence,
        "profile_json": tool.profile_json,
        "status": tool.status.value if tool.status else None,
        "last_run_at": tool.last_run_at.isoformat() if tool.last_run_at else None,
        "last_status": tool.last_status,
        "last_error": tool.last_error,
        "items_total": tool.items_total,
        "robots_txt_ok": tool.robots_txt_ok,
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
        "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
    }
