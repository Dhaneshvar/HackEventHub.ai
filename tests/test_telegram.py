"""Tests for the Telegram bot commands, widgets, security allowlist, and agent loop."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Item, ItemStatus, PriceStatus, Tool, ToolStatus
from app.telegram.agent_loop import execute_tool_call
from app.telegram.commands import is_allowed_user
from app.telegram.widgets import (
    build_item_card_markup,
    build_providers_markup,
    build_tools_markup,
    format_item_card,
)


def test_allowlist_security():
    """Only user IDs explicitly listed in TELEGRAM_ALLOWED_USER_IDS are allowed."""
    original = settings.telegram_allowed_user_ids
    try:
        settings.telegram_allowed_user_ids = "12345,67890"

        # Authorized users
        assert is_allowed_user(12345) is True
        assert is_allowed_user(67890) is True

        # Unauthorized users
        assert is_allowed_user(99999) is False
        assert is_allowed_user(11111) is False
        assert is_allowed_user(None) is False

        # Empty allowed list rejects everyone
        settings.telegram_allowed_user_ids = ""
        assert is_allowed_user(12345) is False
    finally:
        settings.telegram_allowed_user_ids = original


def test_callback_data_size_under_64_bytes():
    """Telegram requires callback_data to be strictly under 64 bytes."""
    markup = build_item_card_markup(item_id=9876543, url="https://example.com")
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                assert len(btn.callback_data.encode("utf-8")) < 64

    # Test tools markup
    tools = [
        Tool(id=123, url="https://example.com", name="Test Tool Very Long Name Here", status=ToolStatus.ACTIVE)
    ]
    tools_markup = build_tools_markup(tools)
    for row in tools_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                assert len(btn.callback_data.encode("utf-8")) < 64

    # Test providers markup
    prov_markup = build_providers_markup(current_active="ollama")
    for row in prov_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                assert len(btn.callback_data.encode("utf-8")) < 64


def test_format_item_card():
    """Format item card returns safe HTML with title and details."""
    item = Item(
        tool_id=1,
        title="AI Global Hackathon <2025>",
        url="https://example.com/ai-hack",
        city="Bangalore",
        is_online=False,
        price_status=PriceStatus.FREE,
        relevance_score=0.92,
        relevance_reason="Matches your interest in AI & Hackathons",
    )
    formatted = format_item_card(item)

    # Verifies HTML escaping of <2025>
    assert "&lt;2025&gt;" in formatted
    assert "AI Global Hackathon" in formatted
    assert "📍 Bangalore" in formatted
    assert "🆓 Free" in formatted
    assert "92% match" in formatted
    assert "Matches your interest in AI &amp; Hackathons" in formatted


@pytest.mark.asyncio
async def test_agent_tool_search_items(db_session: AsyncSession):
    """Agent tool search_items finds matching opportunities."""
    tool = Tool(url="https://source.com", name="Source", status=ToolStatus.ACTIVE)
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    item1 = Item(
        tool_id=tool.id,
        title="Quantum Computing Hackathon",
        url="https://example.com/quantum",
        city="Mumbai",
        price_status=PriceStatus.FREE,
        relevance_score=0.9,
    )
    item2 = Item(
        tool_id=tool.id,
        title="Web3 Workshop",
        url="https://example.com/web3",
        city="Bangalore",
        price_status=PriceStatus.PAID,
        relevance_score=0.5,
    )
    db_session.add(item1)
    db_session.add(item2)
    await db_session.commit()

    # Search for "Quantum"
    res_raw = await execute_tool_call("search_items", {"query": "Quantum"}, session=db_session)
    res = json.loads(res_raw)
    assert len(res) == 1
    assert res[0]["title"] == "Quantum Computing Hackathon"


@pytest.mark.asyncio
async def test_agent_tool_save_item(db_session: AsyncSession):
    """Agent tool save_item saves an item and sets its status to saved."""
    tool = Tool(url="https://source2.com", name="Source2", status=ToolStatus.ACTIVE)
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    item = Item(
        tool_id=tool.id,
        title="Machine Learning Summit",
        url="https://example.com/ml-summit",
        price_status=PriceStatus.FREE,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    res_raw = await execute_tool_call("save_item", {"id": item.id}, session=db_session)
    res = json.loads(res_raw)
    assert res["status"] == "success"

    await db_session.refresh(item)
    assert item.status == ItemStatus.SAVED
