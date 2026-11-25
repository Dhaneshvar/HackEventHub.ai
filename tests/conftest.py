"""Shared test fixtures and configuration."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# Override settings BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["DASHBOARD_TOKEN"] = ""
os.environ["TINYFISH_API_KEY"] = ""

from app.db.models import *  # noqa: E402, F401, F403  - import all models for metadata
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine():
    """Create an in-memory async SQLite engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean async DB session per test."""
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(async_engine, db_session) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the FastAPI app with test DB."""
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _test_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _test_get_session

    # Initialize providers for tests
    from app.providers.router import init_providers, llm_router

    if not llm_router.get_active():
        init_providers()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
