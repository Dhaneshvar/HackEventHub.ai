"""Tests for the Providers API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.seed import seed_defaults


@pytest.mark.asyncio
async def test_list_providers(client: AsyncClient, db_session):
    """List providers returns all three."""
    await seed_defaults(db_session)
    resp = await client.get("/api/providers")
    assert resp.status_code == 200
    data = resp.json()
    names = [p["name"] for p in data["providers"]]
    assert "ollama" in names
    assert "azure" in names
    assert "athena" in names


@pytest.mark.asyncio
async def test_set_active_provider(client: AsyncClient, db_session):
    """Switch active provider."""
    await seed_defaults(db_session)
    resp = await client.put(
        "/api/providers/active",
        json={"provider": "azure"},
    )
    assert resp.status_code == 200
    assert resp.json()["active"] == "azure"

    # Verify via health
    health = await client.get("/api/health")
    assert health.json()["active_provider"] == "azure"


@pytest.mark.asyncio
async def test_set_invalid_provider(client: AsyncClient, db_session):
    """Setting an unknown provider returns 400."""
    await seed_defaults(db_session)
    resp = await client.put(
        "/api/providers/active",
        json={"provider": "nonexistent"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_provider_config(client: AsyncClient, db_session):
    """Update non-secret provider settings."""
    await seed_defaults(db_session)
    resp = await client.put(
        "/api/providers/ollama/config",
        json={"base_url": "http://new-host:11434/v1", "model_name": "new-model"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
