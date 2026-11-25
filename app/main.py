"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import agent_tools, chat, health, interests, items, providers, runs, tools
from app.core.config import settings
from app.db.seed import seed_defaults
from app.db.session import async_session_factory, close_db, init_db
from app.providers.router import init_providers
from app.telegram.bot import start_telegram_bot, stop_telegram_bot

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting HackEventHub.ai...")

    # Init database
    await init_db()
    async with async_session_factory() as session:
        await seed_defaults(session)

    # Init LLM providers
    init_providers()
    logger.info("LLM providers initialized")

    # Start Telegram bot (if token provided in .env)
    await start_telegram_bot()

    yield

    # Shutdown
    await stop_telegram_bot()
    await close_db()
    logger.info("HackEventHub.ai stopped.")


app = FastAPI(
    title="HackEventHub.ai",
    description="Find hackathons, events, and workshops with HackEventHub.ai",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS -- restricted to localhost by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(interests.router, prefix="/api/interests", tags=["interests"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(agent_tools.router, prefix="/api/agent-tools", tags=["agent-tools"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Serve frontend static files if built
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
