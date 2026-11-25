"""Seed default data into the database."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.db.models import AgentToolConfig, Interests, ProviderConfig


async def seed_defaults(session: AsyncSession) -> None:
    """Insert default rows if they don't exist."""

    # Default interests
    result = await session.execute(select(Interests))
    if not result.scalars().first():
        session.add(
            Interests(
                topics_include=["hackathon", "AI", "machine learning", "web development"],
                cities=["Bangalore", "Mumbai", "Online"],
                include_online=True,
                free_only=False,
                min_relevance=0.3,
                digest_time="09:00",
                timezone="Asia/Kolkata",
            )
        )

    # Default provider configs
    for name, base_url, model in [
        ("ollama", "http://localhost:11434/v1", "llama3.1"),
        ("azure", "", ""),
        ("athena", "", ""),
    ]:
        result = await session.execute(select(ProviderConfig).where(ProviderConfig.name == name))
        if not result.scalars().first():
            session.add(
                ProviderConfig(
                    name=name,
                    is_active=(name == "ollama"),
                    fallback_order={"ollama": 0, "azure": 1, "athena": 2}[name],
                    base_url=base_url,
                    model_name=model,
                )
            )

    # Default agent tool configs
    agent_tools = [
        ("search_items", True, "Search stored items by query, city, filters"),
        ("get_item", True, "Get details of a specific item by ID"),
        ("list_new", True, "List new items since a given timestamp"),
        ("list_sources", True, "List enabled and agent-visible tools/sources"),
        ("check_source_live", True, "Fetch and extract from a tool/source now"),
        ("web_search", True, "Search the web via TinyFish (results unverified)"),
        ("fetch_url", True, "Fetch and summarize a URL via TinyFish"),
        ("save_item", True, "Save an item for later"),
    ]
    for func_name, enabled, desc in agent_tools:
        result = await session.execute(
            select(AgentToolConfig).where(AgentToolConfig.function_name == func_name)
        )
        if not result.scalars().first():
            session.add(
                AgentToolConfig(
                    function_name=func_name,
                    enabled=enabled,
                    description=desc,
                )
            )

    await session.commit()
