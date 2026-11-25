"""Agent tools toggle API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import verify_dashboard_token
from app.db.models import AgentToolConfig
from app.db.session import get_session

router = APIRouter(dependencies=[Depends(verify_dashboard_token)])


class ToolToggle(BaseModel):
    enabled: bool


@router.get("")
async def list_agent_tools(session: AsyncSession = Depends(get_session)):
    """List all built-in agent functions with on/off status."""
    result = await session.execute(select(AgentToolConfig))
    tools = result.scalars().all()
    return {
        "tools": [
            {
                "function_name": t.function_name,
                "enabled": t.enabled,
                "description": t.description,
            }
            for t in tools
        ]
    }


@router.put("/{function_name}/toggle")
async def toggle_agent_tool(
    function_name: str,
    body: ToolToggle,
    session: AsyncSession = Depends(get_session),
):
    """Enable or disable a built-in agent tool."""
    result = await session.execute(
        select(AgentToolConfig).where(AgentToolConfig.function_name == function_name)
    )
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(404, f"Agent tool '{function_name}' not found")

    tool.enabled = body.enabled
    session.add(tool)
    await session.commit()
    return {"function_name": tool.function_name, "enabled": tool.enabled}
