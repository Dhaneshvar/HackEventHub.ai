"""Tests for the Tools API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tools_empty(client: AsyncClient):
    """List tools returns empty list initially."""
    resp = await client.get("/api/tools")
    assert resp.status_code == 200
    assert resp.json()["tools"] == []


@pytest.mark.asyncio
async def test_create_tool(client: AsyncClient):
    """Creating a tool returns a draft."""
    resp = await client.post(
        "/api/tools",
        json={"url": "https://devpost.com/hackathons", "note": "Test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "https://devpost.com/hackathons"
    assert data["status"] == "draft"
    assert data["enabled"] is False
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_duplicate_tool(client: AsyncClient):
    """Creating a duplicate tool returns 409."""
    await client.post(
        "/api/tools",
        json={"url": "https://example.com/events"},
    )
    resp = await client.post(
        "/api/tools",
        json={"url": "https://example.com/events"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_tool(client: AsyncClient):
    """Get a tool by ID."""
    create_resp = await client.post(
        "/api/tools",
        json={"url": "https://mlh.io/events"},
    )
    tool_id = create_resp.json()["id"]

    resp = await client.get(f"/api/tools/{tool_id}")
    assert resp.status_code == 200
    assert resp.json()["url"] == "https://mlh.io/events"


@pytest.mark.asyncio
async def test_get_nonexistent_tool(client: AsyncClient):
    """Get a nonexistent tool returns 404."""
    resp = await client.get("/api/tools/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_tool(client: AsyncClient):
    """Update tool fields."""
    create_resp = await client.post(
        "/api/tools",
        json={"url": "https://update-test.com"},
    )
    tool_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/tools/{tool_id}",
        json={"name": "Updated Name", "kind": "hackathon_platform"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    assert resp.json()["kind"] == "hackathon_platform"


@pytest.mark.asyncio
async def test_confirm_tool(client: AsyncClient):
    """Confirming a tool makes it active and enabled."""
    create_resp = await client.post(
        "/api/tools",
        json={"url": "https://confirm-test.com"},
    )
    tool_id = create_resp.json()["id"]

    resp = await client.post(f"/api/tools/{tool_id}/confirm")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_delete_tool(client: AsyncClient):
    """Delete a tool."""
    create_resp = await client.post(
        "/api/tools",
        json={"url": "https://delete-test.com"},
    )
    tool_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/tools/{tool_id}")
    assert resp.status_code == 200

    # Verify it's gone
    resp = await client.get(f"/api/tools/{tool_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_bulk_import(client: AsyncClient):
    """Bulk import creates multiple tools."""
    resp = await client.post(
        "/api/tools/bulk-import",
        json={
            "tools": [
                {"url": "https://bulk1.com", "note": "First"},
                {"url": "https://bulk2.com", "note": "Second"},
                {"url": "https://bulk1.com", "note": "Duplicate"},
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["created"]) == 2
    # Third is a duplicate of the first in the same batch
    assert len(data["skipped"]) == 1
    assert data["skipped"][0] == "https://bulk1.com"
