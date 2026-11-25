"""Tests for database models and seeding."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.models import (
    AgentToolConfig,
    DomainType,
    Interests,
    Item,
    PriceStatus,
    ProviderConfig,
    RunLog,
    RunStatus,
    Tool,
    ToolKind,
    ToolStatus,
)
from app.db.seed import seed_defaults


@pytest.mark.asyncio
async def test_create_tool(db_session: AsyncSession):
    """Can create and retrieve a tool."""
    tool = Tool(
        url="https://devpost.com",
        name="Devpost",
        kind=ToolKind.HACKATHON_PLATFORM,
        domain=DomainType.EVENTS,
        status=ToolStatus.DRAFT,
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    assert tool.id is not None
    assert tool.url == "https://devpost.com"
    assert tool.kind == ToolKind.HACKATHON_PLATFORM


@pytest.mark.asyncio
async def test_create_item(db_session: AsyncSession):
    """Can create and retrieve an item."""
    tool = Tool(url="https://example.com", status=ToolStatus.ACTIVE)
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    item = Item(
        tool_id=tool.id,
        title="Cool Hackathon",
        url="https://example.com/hackathon-1",
        city="Bangalore",
        is_online=False,
        price_status=PriceStatus.FREE,
        relevance_score=0.85,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    assert item.id is not None
    assert item.title == "Cool Hackathon"
    assert item.price_status == PriceStatus.FREE


@pytest.mark.asyncio
async def test_seed_defaults(db_session: AsyncSession):
    """Seeding creates default interests, providers, and agent tools."""
    await seed_defaults(db_session)

    # Check interests
    result = await db_session.execute(select(Interests))
    interests = result.scalars().first()
    assert interests is not None
    assert "hackathon" in interests.topics_include

    # Check provider configs
    result = await db_session.execute(select(ProviderConfig))
    configs = result.scalars().all()
    names = [c.name for c in configs]
    assert "ollama" in names
    assert "azure" in names
    assert "athena" in names

    # Check agent tool configs
    result = await db_session.execute(select(AgentToolConfig))
    tools = result.scalars().all()
    func_names = [t.function_name for t in tools]
    assert "search_items" in func_names
    assert "web_search" in func_names
    assert len(func_names) == 8


@pytest.mark.asyncio
async def test_seed_idempotent(db_session: AsyncSession):
    """Running seed twice doesn't create duplicates."""
    await seed_defaults(db_session)
    await seed_defaults(db_session)

    result = await db_session.execute(select(Interests))
    all_interests = result.scalars().all()
    assert len(all_interests) == 1

    result = await db_session.execute(select(ProviderConfig))
    all_configs = result.scalars().all()
    assert len(all_configs) == 3


@pytest.mark.asyncio
async def test_tool_enum_values(db_session: AsyncSession):
    """Tool kind and domain enums persist correctly."""
    for kind in ToolKind:
        tool = Tool(
            url=f"https://enum-test-{kind.value}.com",
            kind=kind,
            status=ToolStatus.DRAFT,
        )
        db_session.add(tool)
    await db_session.commit()

    result = await db_session.execute(select(Tool))
    tools = result.scalars().all()
    kinds = {t.kind for t in tools}
    assert kinds == set(ToolKind)


@pytest.mark.asyncio
async def test_run_log(db_session: AsyncSession):
    """Can create run log entries."""
    tool = Tool(url="https://run-log-test.com", status=ToolStatus.ACTIVE)
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    log = RunLog(
        tool_id=tool.id,
        status=RunStatus.SUCCESS,
        items_found=5,
        items_new=3,
        fetch_method="httpx",
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)

    assert log.id is not None
    assert log.status == RunStatus.SUCCESS
