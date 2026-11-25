"""Interests & Schedule preferences API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import verify_dashboard_token
from app.db.models import Interests
from app.db.session import get_session

router = APIRouter(dependencies=[Depends(verify_dashboard_token)])


class InterestsUpdate(BaseModel):
    topics_include: list[str] | None = None
    topics_exclude: list[str] | None = None
    cities: list[str] | None = None
    include_online: bool | None = None
    free_only: bool | None = None
    skill_level: str | None = None
    max_items_per_digest: int | None = None
    min_relevance: float | None = None
    instant_alerts: bool | None = None
    digest_time: str | None = None
    timezone: str | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


@router.get("")
async def get_interests(session: AsyncSession = Depends(get_session)):
    """Get the user interests and digest preferences."""
    result = await session.execute(select(Interests))
    interests = result.scalars().first()
    if not interests:
        interests = Interests()
        session.add(interests)
        await session.commit()
        await session.refresh(interests)
    return _interests_to_dict(interests)


@router.put("")
async def update_interests(
    body: InterestsUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update user interests and digest schedule settings."""
    result = await session.execute(select(Interests))
    interests = result.scalars().first()
    if not interests:
        interests = Interests()
        session.add(interests)

    for field_name, value in body.model_dump(exclude_unset=True).items():
        setattr(interests, field_name, value)

    session.add(interests)
    await session.commit()
    await session.refresh(interests)
    return _interests_to_dict(interests)


def _interests_to_dict(interests: Interests) -> dict[str, Any]:
    return {
        "id": interests.id,
        "topics_include": interests.topics_include or [],
        "topics_exclude": interests.topics_exclude or [],
        "cities": interests.cities or [],
        "include_online": interests.include_online,
        "free_only": interests.free_only,
        "skill_level": interests.skill_level,
        "max_items_per_digest": interests.max_items_per_digest,
        "min_relevance": interests.min_relevance,
        "instant_alerts": interests.instant_alerts,
        "digest_time": interests.digest_time,
        "timezone": interests.timezone,
        "quiet_hours_start": interests.quiet_hours_start,
        "quiet_hours_end": interests.quiet_hours_end,
    }
