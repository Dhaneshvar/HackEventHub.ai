"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_dashboard_token(
    authorization: str | None = Header(None, alias="Authorization"),
) -> None:
    """Verify the dashboard bearer token if configured."""
    if not settings.dashboard_token:
        return  # No token configured = open (localhost only)
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != settings.dashboard_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
