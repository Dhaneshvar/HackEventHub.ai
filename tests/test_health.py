"""Tests for the health endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint returns ok status."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "active_provider" in data


@pytest.mark.asyncio
async def test_health_shows_active_provider(client: AsyncClient):
    """Health endpoint shows the active LLM provider."""
    resp = await client.get("/api/health")
    data = resp.json()
    assert data["active_provider"] == "ollama"
