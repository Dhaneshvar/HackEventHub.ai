"""Tests for the dashboard authentication."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings
from app.db.models import *  # noqa
from app.db.session import get_session
from app.main import app


@pytest.mark.asyncio
async def test_dashboard_token_required():
    """When DASHBOARD_TOKEN is set, unauthenticated requests are rejected."""
    original_token = settings.dashboard_token
    settings.dashboard_token = "test-secret-token"

    try:
        engine = create_async_engine(
            "sqlite+aiosqlite://",
            connect_args={"check_same_thread": False},
        )
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def _test_session():
            async with factory() as s:
                yield s

        app.dependency_overrides[get_session] = _test_session

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # No token -> 401
            resp = await ac.get("/api/tools")
            assert resp.status_code == 401

            # Wrong token -> 401
            resp = await ac.get("/api/tools", headers={"Authorization": "Bearer wrong-token"})
            assert resp.status_code == 401

            # Correct token -> 200
            resp = await ac.get(
                "/api/tools",
                headers={"Authorization": "Bearer test-secret-token"},
            )
            assert resp.status_code == 200

        app.dependency_overrides.clear()
        await engine.dispose()
    finally:
        settings.dashboard_token = original_token


@pytest.mark.asyncio
async def test_health_no_auth_needed(client: AsyncClient):
    """Health endpoint does not require auth."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
