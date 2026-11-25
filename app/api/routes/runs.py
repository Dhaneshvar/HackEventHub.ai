"""Run logs API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.api.deps import verify_dashboard_token
from app.db.models import RunLog, RunStatus
from app.db.session import get_session

router = APIRouter(dependencies=[Depends(verify_dashboard_token)])


@router.get("")
async def list_runs(
    session: AsyncSession = Depends(get_session),
    tool_id: int | None = None,
    status: RunStatus | None = None,
    limit: int = Query(default=50, le=200),
):
    """List crawl and digest execution logs."""
    stmt = select(RunLog)
    if tool_id:
        stmt = stmt.where(RunLog.tool_id == tool_id)
    if status:
        stmt = stmt.where(RunLog.status == status)

    stmt = stmt.order_by(col(RunLog.started_at).desc()).limit(limit)
    result = await session.execute(stmt)
    runs = result.scalars().all()
    return {"runs": [_run_to_dict(r) for r in runs]}


@router.post("")
async def trigger_run_all(session: AsyncSession = Depends(get_session)):
    """Trigger a crawl of all enabled tools immediately."""
    # In Phase 3, this queues APScheduler jobs. For now, acknowledge request.
    return {"status": "triggered", "message": "Crawl queued for all active tools"}


def _run_to_dict(log: RunLog) -> dict[str, Any]:
    return {
        "id": log.id,
        "tool_id": log.tool_id,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "finished_at": log.finished_at.isoformat() if log.finished_at else None,
        "status": log.status.value if log.status else None,
        "items_found": log.items_found,
        "items_new": log.items_new,
        "error": log.error,
        "fetch_method": log.fetch_method,
        "cost_units": log.cost_units,
    }
