"""Items API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.api.deps import verify_dashboard_token
from app.db.models import DomainType, Item, ItemStatus, PriceStatus, SavedItem, utc_now
from app.db.session import get_session

router = APIRouter(dependencies=[Depends(verify_dashboard_token)])


class ItemStatusUpdate(BaseModel):
    status: ItemStatus


@router.get("")
async def list_items(
    session: AsyncSession = Depends(get_session),
    domain: DomainType | None = None,
    tool_id: int | None = None,
    city: str | None = None,
    is_online: bool | None = None,
    price_status: PriceStatus | None = None,
    min_relevance: float | None = None,
    status: ItemStatus | None = None,
    query: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List items with filtering and search."""
    stmt = select(Item)
    if domain:
        stmt = stmt.where(Item.domain == domain)
    if tool_id:
        stmt = stmt.where(Item.tool_id == tool_id)
    if city:
        stmt = stmt.where(col(Item.city).ilike(f"%{city}%"))
    if is_online is not None:
        stmt = stmt.where(Item.is_online == is_online)
    if price_status:
        stmt = stmt.where(Item.price_status == price_status)
    if min_relevance is not None:
        stmt = stmt.where(Item.relevance_score >= min_relevance)
    if status:
        stmt = stmt.where(Item.status == status)
    if query:
        stmt = stmt.where(
            (col(Item.title).ilike(f"%{query}%"))
            | (col(Item.description_snippet).ilike(f"%{query}%"))
            | (col(Item.organizer).ilike(f"%{query}%"))
        )

    stmt = stmt.order_by(col(Item.first_seen_at).desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    items = result.scalars().all()
    return {"items": [_item_to_dict(i) for i in items]}


@router.get("/{item_id}")
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return _item_to_dict(item)


@router.post("/{item_id}/save")
async def save_item(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    item.status = ItemStatus.SAVED
    session.add(item)

    saved_res = await session.execute(select(SavedItem).where(SavedItem.item_id == item_id))
    if not saved_res.scalars().first():
        session.add(SavedItem(item_id=item_id, saved_at=utc_now()))

    await session.commit()
    return {"ok": True, "item": _item_to_dict(item)}


@router.post("/{item_id}/hide")
async def hide_item(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    item.status = ItemStatus.HIDDEN
    session.add(item)
    await session.commit()
    return {"ok": True, "item": _item_to_dict(item)}


def _item_to_dict(item: Item) -> dict[str, Any]:
    return {
        "id": item.id,
        "domain": item.domain.value if item.domain else None,
        "tool_id": item.tool_id,
        "title": item.title,
        "url": item.url,
        "location_text": item.location_text,
        "is_online": item.is_online,
        "city": item.city,
        "start_date": item.start_date.isoformat() if item.start_date else None,
        "end_date": item.end_date.isoformat() if item.end_date else None,
        "price_status": item.price_status.value if item.price_status else None,
        "price_text": item.price_text,
        "organizer": item.organizer,
        "description_snippet": item.description_snippet,
        "tags": item.tags or [],
        "first_seen_at": item.first_seen_at.isoformat() if item.first_seen_at else None,
        "last_seen_at": item.last_seen_at.isoformat() if item.last_seen_at else None,
        "relevance_score": item.relevance_score,
        "relevance_reason": item.relevance_reason,
        "status": item.status.value if item.status else None,
    }
