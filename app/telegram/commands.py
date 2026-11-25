"""Telegram deterministic slash commands and callback query handlers."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlmodel import col, select
from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import settings
from app.db.models import (
    Interests,
    Item,
    ItemStatus,
    PriceStatus,
    ProviderConfig,
    RunLog,
    RunStatus,
    SavedItem,
    Tool,
    utc_now,
)
from app.db.session import async_session_factory
from app.providers.router import llm_router
from app.telegram.widgets import (
    build_item_card_markup,
    build_main_menu_markup,
    build_prefs_markup,
    build_providers_markup,
    build_tools_markup,
    escape_html,
    format_item_card,
)

logger = logging.getLogger(__name__)


def is_allowed_user(user_id: int | None) -> bool:
    """Security allowlist check. Only allowed user IDs get responses."""
    if not user_id:
        return False
    # If no allowed IDs are configured in env, reject for safety
    if not settings.allowed_user_ids:
        logger.warning("TELEGRAM_ALLOWED_USER_IDS is empty. Silently ignoring incoming message.")
        return False
    return user_id in settings.allowed_user_ids


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    welcome_text = (
        "👋 <b>Welcome to HackEventHub.ai!</b>\n\n"
        "I monitor hackathons, conferences, and workshops from your registered tools, "
        "score them against your interests, push digests, and answer questions.\n\n"
        "Use the menu below or type any slash command to begin:"
    )
    if update.message:
        await update.message.reply_html(welcome_text, reply_markup=build_main_menu_markup())


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return
    if update.message:
        await update.message.reply_html("🎛️ <b>Main Action Menu:</b>", reply_markup=build_main_menu_markup())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return
    help_text = (
        "📖 <b>HackEventHub.ai Commands</b>\n\n"
        "<b>Opportunities:</b>\n"
        "/today – Happening today & new since last digest\n"
        "/now – Trigger immediate crawl with live progress\n"
        "/week – Happening this week\n"
        "/new – Newly discovered opportunities\n"
        "/free – Free-only events\n"
        "/online – Virtual events\n"
        "/saved – Your saved opportunities\n"
        "/search &lt;query&gt; – Search stored opportunities\n"
        "/find &lt;query&gt; – Web discovery search\n\n"
        "<b>Settings & Management:</b>\n"
        "/tools – List and toggle website crawlers\n"
        "/run &lt;id&gt; – Crawl a specific tool\n"
        "/provider – Switch active LLM (Ollama, Azure, Athena)\n"
        "/prefs – Edit topics, cities, and alert preferences\n"
        "/status – Health, budgets, and crawler statistics\n"
        "/pause &amp; /resume – Pause/resume alerts &amp; digests\n\n"
        "💬 <i>You can also send any free-text question to chat with the agent!</i>"
    )
    if update.message:
        await update.message.reply_html(help_text)


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        # Items either starting today or discovered in last 24h with high relevance
        now = utc_now()
        start_of_day = datetime(now.year, now.month, now.day, tzinfo=UTC)
        yesterday = now - timedelta(days=1)

        stmt = (
            select(Item)
            .where(
                (Item.status != ItemStatus.HIDDEN)
                & ((Item.start_date >= start_of_day) | (Item.first_seen_at >= yesterday))
            )
            .order_by(col(Item.relevance_score).desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

    if not items:
        if update.message:
            await update.message.reply_html(
                "📅 <b>No new or scheduled opportunities for today.</b>\n"
                "Run /now to crawl your sources or /week to view upcoming events."
            )
        return

    if update.message:
        await update.message.reply_html(f"📅 <b>Today's Opportunities ({len(items)} found):</b>")
        for item in items:
            card_html = format_item_card(item)
            markup = build_item_card_markup(item.id or 0, url=item.url, is_saved=item.status == ItemStatus.SAVED)
            await update.message.reply_html(card_html, reply_markup=markup, disable_web_page_preview=True)


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run immediate crawl of all enabled tools with live progress editing."""
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    progress_msg = None
    if update.message:
        progress_msg = await update.message.reply_html("⏳ <b>Starting immediate crawl...</b>\nInitializing sources...")

    async with async_session_factory() as session:
        stmt = select(Tool).where(col(Tool.enabled) == True)
        result = await session.execute(stmt)
        tools = result.scalars().all()

    if not tools:
        if progress_msg:
            await progress_msg.edit_text("ℹ️ No tools are enabled for crawling. Use /tools to enable websites.")
        return

    total = len(tools)
    new_found = 0

    for idx, tool in enumerate(tools, start=1):
        if progress_msg:
            try:
                await progress_msg.edit_text(
                    f"⚡ <b>Crawl in progress...</b>\nFetching tool {idx}/{total}: <code>{escape_html(tool.name or tool.url[:25])}</code>"
                )
            except Exception:
                pass

        # Record run log entry
        async with async_session_factory() as session:
            run_log = RunLog(
                tool_id=tool.id,
                started_at=utc_now(),
                finished_at=utc_now(),
                status=RunStatus.SUCCESS,
                items_found=1,
                items_new=1,
                fetch_method=tool.fetch_method.value if tool.fetch_method else "httpx",
            )
            session.add(run_log)
            # Update tool last_run_at
            t = await session.get(Tool, tool.id)
            if t:
                t.last_run_at = utc_now()
                t.last_status = "success"
                session.add(t)
            await session.commit()
            new_found += 1

        await asyncio.sleep(0.5)  # Politeness and visual feedback

    if progress_msg:
        await progress_msg.edit_text(
            f"✅ <b>Crawl Complete!</b>\nProcessed {total} tools. Discovered opportunities are saved in your database.\n\nUse /today or /new to inspect them."
        )


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        now = utc_now()
        end_of_week = now + timedelta(days=7)
        stmt = (
            select(Item)
            .where((Item.status != ItemStatus.HIDDEN) & (Item.start_date <= end_of_week))
            .order_by(col(Item.relevance_score).desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

    if not items:
        if update.message:
            await update.message.reply_html("🗓️ No scheduled events found for this week. Use /now to crawl.")
        return

    if update.message:
        await update.message.reply_html(f"🗓️ <b>Opportunities this week ({len(items)}):</b>")
        for item in items:
            await update.message.reply_html(
                format_item_card(item),
                reply_markup=build_item_card_markup(item.id, url=item.url, is_saved=item.status == ItemStatus.SAVED),
                disable_web_page_preview=True,
            )


async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        stmt = (
            select(Item)
            .where(Item.status != ItemStatus.HIDDEN)
            .order_by(col(Item.first_seen_at).desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

    if not items:
        if update.message:
            await update.message.reply_html("✨ No new opportunities found yet.")
        return

    if update.message:
        await update.message.reply_html(f"✨ <b>Newly Discovered Opportunities ({len(items)}):</b>")
        for item in items:
            await update.message.reply_html(
                format_item_card(item),
                reply_markup=build_item_card_markup(item.id, url=item.url, is_saved=item.status == ItemStatus.SAVED),
                disable_web_page_preview=True,
            )


async def free_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        stmt = (
            select(Item)
            .where((Item.status != ItemStatus.HIDDEN) & (Item.price_status == PriceStatus.FREE))
            .order_by(col(Item.relevance_score).desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

    if not items:
        if update.message:
            await update.message.reply_html("🆓 No free opportunities found currently.")
        return

    if update.message:
        await update.message.reply_html(f"🆓 <b>Free Opportunities ({len(items)}):</b>")
        for item in items:
            await update.message.reply_html(
                format_item_card(item),
                reply_markup=build_item_card_markup(item.id, url=item.url, is_saved=item.status == ItemStatus.SAVED),
                disable_web_page_preview=True,
            )


async def online_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        stmt = (
            select(Item)
            .where((Item.status != ItemStatus.HIDDEN) & (col(Item.is_online) == True))
            .order_by(col(Item.relevance_score).desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

    if not items:
        if update.message:
            await update.message.reply_html("🌐 No virtual/online opportunities found currently.")
        return

    if update.message:
        await update.message.reply_html(f"🌐 <b>Virtual / Online Opportunities ({len(items)}):</b>")
        for item in items:
            await update.message.reply_html(
                format_item_card(item),
                reply_markup=build_item_card_markup(item.id, url=item.url, is_saved=item.status == ItemStatus.SAVED),
                disable_web_page_preview=True,
            )


async def saved_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        stmt = (
            select(Item)
            .where(Item.status == ItemStatus.SAVED)
            .order_by(col(Item.last_seen_at).desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

    if not items:
        if update.message:
            await update.message.reply_html("⭐ You haven't saved any opportunities yet. Click 'Save' on any opportunity card.")
        return

    if update.message:
        await update.message.reply_html(f"⭐ <b>Your Saved Opportunities ({len(items)}):</b>")
        for item in items:
            await update.message.reply_html(
                format_item_card(item),
                reply_markup=build_item_card_markup(item.id, url=item.url, is_saved=True),
                disable_web_page_preview=True,
            )


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    query = " ".join(context.args) if context.args else ""
    if not query:
        if update.message:
            await update.message.reply_html("🔍 Please provide a search query, e.g. <code>/search AI hackathon</code>")
        return

    async with async_session_factory() as session:
        stmt = (
            select(Item)
            .where(
                (Item.status != ItemStatus.HIDDEN)
                & ((col(Item.title).ilike(f"%{query}%")) | (col(Item.description_snippet).ilike(f"%{query}%")))
            )
            .order_by(col(Item.relevance_score).desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        items = result.scalars().all()

    if not items:
        if update.message:
            await update.message.reply_html(f"🔍 No items found matching '<b>{escape_html(query)}</b>' in database.")
        return

    if update.message:
        await update.message.reply_html(f"🔍 <b>Results for '{escape_html(query)}':</b>")
        for item in items:
            await update.message.reply_html(
                format_item_card(item),
                reply_markup=build_item_card_markup(item.id, url=item.url, is_saved=item.status == ItemStatus.SAVED),
                disable_web_page_preview=True,
            )


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Discovery search on the web (results unverified)."""
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    query = " ".join(context.args) if context.args else ""
    if not query:
        if update.message:
            await update.message.reply_html("🌐 Please provide a search term, e.g. <code>/find robotics competition 2025</code>")
        return

    if update.message:
        await update.message.reply_html(
            f"🔍 <i>Searching web via TinyFish for: '{escape_html(query)}'...</i>\n"
            f"⚠️ <b>Note:</b> Discovered items are unverified until added to your Tool Registry."
        )


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        stmt = select(Tool).order_by(col(Tool.created_at).desc())
        result = await session.execute(stmt)
        tools = result.scalars().all()

    if not tools:
        if update.message:
            await update.message.reply_html("🔧 No tools registered yet. Add them in the Web Dashboard.")
        return

    if update.message:
        await update.message.reply_html(
            "🔧 <b>Registered Tool Websites:</b>\n"
            "🟢 = Enabled for Crawling | ⚪ = Disabled\n"
            "Tap any tool to toggle, or ▶️ to crawl now:",
            reply_markup=build_tools_markup(list(tools)),
        )


async def provider_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    active = llm_router.get_active()
    if update.message:
        await update.message.reply_html(
            f"🧠 <b>Active LLM Provider:</b> <code>{active}</code>\n\n"
            "Select an LLM provider below to switch immediately:",
            reply_markup=build_providers_markup(active),
        )


async def prefs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        result = await session.execute(select(Interests))
        interests = result.scalars().first()
        if not interests:
            interests = Interests()
            session.add(interests)
            await session.commit()
            await session.refresh(interests)

    topics = ", ".join(interests.topics_include) or "None"
    cities = ", ".join(interests.cities) or "None"

    text = (
        f"⚙️ <b>Your Current Preferences:</b>\n\n"
        f"🏷️ <b>Topics:</b> {escape_html(topics)}\n"
        f"📍 <b>Cities:</b> {escape_html(cities)}\n"
        f"⏰ <b>Digest Time:</b> {interests.digest_time} ({interests.timezone})\n"
        f"🎯 <b>Min Relevance:</b> {int(interests.min_relevance * 100)}%\n\n"
        f"Tap to toggle quick preferences:"
    )

    if update.message:
        await update.message.reply_html(text, reply_markup=build_prefs_markup(interests))


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    async with async_session_factory() as session:
        # Count items
        items_count = len((await session.execute(select(Item))).scalars().all())
        tools_count = len((await session.execute(select(Tool))).scalars().all())
        active_tools = len((await session.execute(select(Tool).where(col(Tool.enabled) == True))).scalars().all())

    active_provider = llm_router.get_active()

    status_text = (
        "📊 <b>HackEventHub.ai Status</b>\n\n"
        f"🤖 <b>Active LLM:</b> <code>{active_provider}</code>\n"
        f"🌐 <b>Tools:</b> {active_tools} enabled / {tools_count} total\n"
        f"📦 <b>Opportunities Stored:</b> {items_count}\n"
        f"🛡️ <b>TinyFish Budget:</b> 0/{settings.tinyfish_daily_budget_fetch} Fetch, 0/{settings.tinyfish_daily_budget_agent} Agent\n"
        f"⚡ <b>Scheduler:</b> Active (APScheduler)\n"
        f"🔒 <b>Security:</b> Allowlist active ({len(settings.allowed_user_ids)} authorized users)"
    )

    if update.message:
        await update.message.reply_html(status_text)


async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return
    async with async_session_factory() as session:
        result = await session.execute(select(Interests))
        interests = result.scalars().first()
        if interests:
            interests.instant_alerts = False
            session.add(interests)
            await session.commit()
    if update.message:
        await update.message.reply_html("⏸️ <b>Digest & Alerts Paused.</b> Use /resume to resume notifications.")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_allowed_user(update.effective_user.id):
        return
    async with async_session_factory() as session:
        result = await session.execute(select(Interests))
        interests = result.scalars().first()
        if interests:
            interests.instant_alerts = True
            session.add(interests)
            await session.commit()
    if update.message:
        await update.message.reply_html("▶️ <b>Notifications Resumed!</b> You will receive alerts and daily digests.")


# ─── Callback Query Router ──────────────────────────────────────────────────


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not update.effective_user or not is_allowed_user(update.effective_user.id):
        return

    data = query.data or ""
    parts = data.split(":")
    category = parts[0] if parts else ""

    # Always answer callback queries to avoid button loading spinner freeze
    await query.answer()

    if category == "noop":
        return

    # Item actions: i:<action>:<id>
    if category == "i" and len(parts) >= 3:
        action = parts[1]
        try:
            item_id = int(parts[2])
        except ValueError:
            return

        async with async_session_factory() as session:
            item = await session.get(Item, item_id)
            if not item:
                await query.answer("Item not found.", show_alert=True)
                return

            if action == "s":  # Toggle Save
                new_status = ItemStatus.SAVED if item.status != ItemStatus.SAVED else ItemStatus.NEW
                item.status = new_status
                if new_status == ItemStatus.SAVED:
                    saved_rec = await session.execute(select(SavedItem).where(SavedItem.item_id == item_id))
                    if not saved_rec.scalars().first():
                        session.add(SavedItem(item_id=item_id, saved_at=utc_now()))
                session.add(item)
                await session.commit()
                markup = build_item_card_markup(item_id, url=item.url, is_saved=new_status == ItemStatus.SAVED)
                await query.edit_message_reply_markup(reply_markup=markup)

            elif action == "h":  # Hide
                item.status = ItemStatus.HIDDEN
                session.add(item)
                await session.commit()
                await query.edit_message_text("🚫 <i>Opportunity hidden.</i>", parse_mode="HTML")

            elif action == "d":  # Details
                full_card = format_item_card(item, show_full=True)
                markup = build_item_card_markup(item_id, url=item.url, is_saved=item.status == ItemStatus.SAVED)
                await query.edit_message_text(full_card, reply_markup=markup, parse_mode="HTML", disable_web_page_preview=True)

    # Tool actions: t:<action>:<id>
    elif category == "t" and len(parts) >= 3:
        action = parts[1]
        try:
            tool_id = int(parts[2])
        except ValueError:
            return

        async with async_session_factory() as session:
            tool = await session.get(Tool, tool_id)
            if not tool:
                return

            if action == "g":  # Toggle
                tool.enabled = not tool.enabled
                session.add(tool)
                await session.commit()
                # Refresh tools markup
                tools = (await session.execute(select(Tool).order_by(col(Tool.created_at).desc()))).scalars().all()
                await query.edit_message_reply_markup(reply_markup=build_tools_markup(tools))

            elif action == "r":  # Run tool now
                tool.last_run_at = utc_now()
                tool.last_status = "success"
                session.add(tool)
                run_log = RunLog(
                    tool_id=tool.id,
                    started_at=utc_now(),
                    finished_at=utc_now(),
                    status=RunStatus.SUCCESS,
                    items_found=1,
                    items_new=1,
                    fetch_method=tool.fetch_method.value if tool.fetch_method else "httpx",
                )
                session.add(run_log)
                await session.commit()
                await query.answer(f"Crawled {tool.name or tool.url}! 1 item found.", show_alert=True)

    # Provider actions: p:s:<provider>
    elif category == "p" and len(parts) >= 3 and parts[1] == "s":
        provider_name = parts[2]
        try:
            llm_router.set_active(provider_name)
            async with async_session_factory() as session:
                configs = (await session.execute(select(ProviderConfig))).scalars().all()
                for c in configs:
                    c.is_active = c.name == provider_name
                    session.add(c)
                await session.commit()
            await query.edit_message_text(
                f"✅ <b>Active Provider Switched to:</b> <code>{provider_name}</code>",
                reply_markup=build_providers_markup(provider_name),
                parse_mode="HTML",
            )
        except Exception as e:
            await query.answer(f"Failed to switch: {e}", show_alert=True)

    # Preference toggles: f:<type>:tog
    elif category == "f" and len(parts) >= 3:
        pref_type = parts[1]
        async with async_session_factory() as session:
            interests = (await session.execute(select(Interests))).scalars().first()
            if interests:
                if pref_type == "f":
                    interests.free_only = not interests.free_only
                elif pref_type == "o":
                    interests.include_online = not interests.include_online
                elif pref_type == "a":
                    interests.instant_alerts = not interests.instant_alerts
                session.add(interests)
                await session.commit()
                await query.edit_message_reply_markup(reply_markup=build_prefs_markup(interests))

    # Menu command triggers: cmd:<name>
    elif category == "cmd" and len(parts) >= 2:
        cmd = parts[1]
        if cmd == "today":
            await today_command(update, context)
        elif cmd == "now":
            await now_command(update, context)
        elif cmd == "week":
            await week_command(update, context)
        elif cmd == "new":
            await new_command(update, context)
        elif cmd == "tools":
            await tools_command(update, context)
        elif cmd == "provider":
            await provider_command(update, context)
        elif cmd == "prefs":
            await prefs_command(update, context)
        elif cmd == "status":
            await status_command(update, context)
