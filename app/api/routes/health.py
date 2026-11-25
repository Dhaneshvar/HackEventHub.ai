"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.providers.router import llm_router

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    active_provider = llm_router.get_active()
    return {
        "status": "ok",
        "version": "0.1.0",
        "active_provider": active_provider,
    }
