"""Database models using SQLModel (SQLAlchemy 2.x + Pydantic v2)."""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlmodel import JSON, Column, Field, SQLModel


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)

# ─── Enums ───────────────────────────────────────────────────────────────


class ToolKind(enum.StrEnum):
    HACKATHON_PLATFORM = "hackathon_platform"
    EVENT_AGGREGATOR = "event_aggregator"
    WORKSHOP_TRAINING = "workshop_training"
    CONFERENCE = "conference"
    MEETUP_COMMUNITY = "meetup_community"
    UNIVERSITY_OR_ORG = "university_or_org"
    JOB_BOARD = "job_board"
    NEWSLETTER_OR_BLOG = "newsletter_or_blog"
    OTHER = "other"


class DomainType(enum.StrEnum):
    EVENTS = "events"
    JOBS = "jobs"


class FetchMethod(enum.StrEnum):
    AUTO = "auto"
    RSS = "rss"
    JSONLD = "jsonld"
    TINYFISH_FETCH = "tinyfish_fetch"
    TINYFISH_AGENT = "tinyfish_agent"
    HTTPX = "httpx"


class PriceStatus(enum.StrEnum):
    FREE = "free"
    PAID = "paid"
    UNKNOWN = "unknown"


class ItemStatus(enum.StrEnum):
    NEW = "new"
    SENT = "sent"
    SAVED = "saved"
    HIDDEN = "hidden"


class ToolStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    BLOCKED = "blocked"
    ERROR = "error"


class RunStatus(enum.StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# ─── Tool ────────────────────────────────────────────────────────────────


class Tool(SQLModel, table=True):
    __tablename__ = "tools"

    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    name: str = ""
    kind: ToolKind = ToolKind.OTHER
    domain: DomainType = DomainType.EVENTS
    description: str = ""
    fetch_method: FetchMethod = FetchMethod.AUTO
    listing_urls: list[str] = Field(default_factory=list, sa_column=Column(JSON, default="[]"))
    needs_js: bool = False
    crawl_interval_minutes: int = Field(default=360)
    enabled: bool = False
    agent_visible: bool = True
    is_preset: bool = False
    user_note: str = ""
    profile_confidence: float = 0.0
    profile_json: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    status: ToolStatus = ToolStatus.DRAFT
    last_run_at: datetime | None = None
    last_status: str = ""
    last_error: str = ""
    items_total: int = 0
    robots_txt_ok: bool | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# ─── Item ────────────────────────────────────────────────────────────────


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: int | None = Field(default=None, primary_key=True)
    domain: DomainType = DomainType.EVENTS
    tool_id: int = Field(foreign_key="tools.id", index=True)
    title: str
    url: str = Field(index=True, unique=True)
    location_text: str = ""
    is_online: bool = False
    city: str = ""
    start_date: datetime | None = None
    end_date: datetime | None = None
    price_status: PriceStatus = PriceStatus.UNKNOWN
    price_text: str = ""
    organizer: str = ""
    description_snippet: str = ""
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, default="[]"))
    first_seen_at: datetime = Field(default_factory=utc_now)
    last_seen_at: datetime = Field(default_factory=utc_now)
    relevance_score: float = 0.0
    relevance_reason: str = ""
    status: ItemStatus = ItemStatus.NEW
    raw_hash: str = ""


# ─── Interests ───────────────────────────────────────────────────────────


class Interests(SQLModel, table=True):
    __tablename__ = "interests"

    id: int | None = Field(default=None, primary_key=True)
    topics_include: list[str] = Field(default_factory=list, sa_column=Column(JSON, default="[]"))
    topics_exclude: list[str] = Field(default_factory=list, sa_column=Column(JSON, default="[]"))
    cities: list[str] = Field(default_factory=list, sa_column=Column(JSON, default="[]"))
    include_online: bool = True
    free_only: bool = False
    skill_level: str = "any"
    max_items_per_digest: int = 20
    min_relevance: float = 0.3
    instant_alerts: bool = False
    digest_time: str = "09:00"
    timezone: str = "UTC"
    quiet_hours_start: str = ""
    quiet_hours_end: str = ""


# ─── RunLog ──────────────────────────────────────────────────────────────


class RunLog(SQLModel, table=True):
    __tablename__ = "run_logs"

    id: int | None = Field(default=None, primary_key=True)
    tool_id: int = Field(foreign_key="tools.id", index=True)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    status: RunStatus = RunStatus.RUNNING
    items_found: int = 0
    items_new: int = 0
    error: str = ""
    fetch_method: str = ""
    cost_units: float = 0.0


# ─── ProviderCall ────────────────────────────────────────────────────────


class ProviderCall(SQLModel, table=True):
    __tablename__ = "provider_calls"

    id: int | None = Field(default=None, primary_key=True)
    provider: str
    model: str = ""
    task: str = ""
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    status: str = "ok"
    error: str = ""


# ─── AgentToolConfig ─────────────────────────────────────────────────────


class AgentToolConfig(SQLModel, table=True):
    __tablename__ = "agent_tool_configs"

    id: int | None = Field(default=None, primary_key=True)
    function_name: str = Field(unique=True, index=True)
    enabled: bool = True
    description: str = ""


# ─── ProviderConfig ──────────────────────────────────────────────────────


class ProviderConfig(SQLModel, table=True):
    __tablename__ = "provider_configs"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    is_active: bool = False
    fallback_order: int = 0
    base_url: str = ""
    model_name: str = ""
    has_api_key: bool = False
    supports_tool_calling: bool | None = None
    supports_json_mode: bool | None = None
    last_test_at: datetime | None = None
    last_test_latency_ms: float | None = None
    last_test_error: str = ""
    # Per-task routing
    task_profiling: str = ""
    task_extraction: str = ""
    task_relevance: str = ""
    task_chat: str = ""


# ─── SavedItem ───────────────────────────────────────────────────────────


class SavedItem(SQLModel, table=True):
    __tablename__ = "saved_items"

    id: int | None = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="items.id", unique=True, index=True)
    saved_at: datetime = Field(default_factory=utc_now)
    note: str = ""
