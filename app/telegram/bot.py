"""Telegram Bot Application lifecycle, command setup, and long-polling runner."""

from __future__ import annotations

import asyncio
import logging

from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.core.config import settings
from app.telegram.agent_loop import handle_agent_chat
from app.telegram.commands import (
    find_command,
    free_command,
    handle_callback_query,
    help_command,
    menu_command,
    new_command,
    now_command,
    online_command,
    pause_command,
    prefs_command,
    provider_command,
    resume_command,
    saved_command,
    search_command,
    start_command,
    status_command,
    today_command,
    tools_command,
    week_command,
)

logger = logging.getLogger(__name__)

_bot_app: Application | None = None
_bot_task: asyncio.Task | None = None


async def setup_bot_commands(app: Application) -> None:
    """Register slash commands in Telegram's autocomplete menu."""
    commands = [
        BotCommand("today", "Today's opportunities & new items"),
        BotCommand("now", "Run immediate crawl with live progress"),
        BotCommand("week", "Opportunities scheduled for this week"),
        BotCommand("new", "Newly discovered opportunities"),
        BotCommand("free", "Filter for free events"),
        BotCommand("online", "Filter for virtual/online events"),
        BotCommand("saved", "View your saved opportunities"),
        BotCommand("search", "Search stored opportunities"),
        BotCommand("find", "Search web via TinyFish"),
        BotCommand("tools", "Manage registered crawler websites"),
        BotCommand("provider", "Switch active LLM provider"),
        BotCommand("prefs", "Edit topics, cities, and alert preferences"),
        BotCommand("status", "System stats, budgets, and crawl health"),
        BotCommand("pause", "Pause digest & instant alerts"),
        BotCommand("resume", "Resume digest & instant alerts"),
        BotCommand("menu", "Show interactive main button menu"),
        BotCommand("help", "Help and command reference"),
    ]
    try:
        await app.bot.set_my_commands(commands)
        logger.info("Telegram command menu registered successfully.")
    except Exception as e:
        logger.warning("Could not register Telegram commands: %s", e)


def create_telegram_app() -> Application:
    """Build the PTB Application with all handlers."""
    token = settings.telegram_bot_token
    app = Application.builder().token(token).build()

    # Slash command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("now", now_command))
    app.add_handler(CommandHandler("week", week_command))
    app.add_handler(CommandHandler("new", new_command))
    app.add_handler(CommandHandler("free", free_command))
    app.add_handler(CommandHandler("online", online_command))
    app.add_handler(CommandHandler("saved", saved_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("find", find_command))
    app.add_handler(CommandHandler("tools", tools_command))
    app.add_handler(CommandHandler("provider", provider_command))
    app.add_handler(CommandHandler("prefs", prefs_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("resume", resume_command))

    # Button widget callbacks
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Free-text chat to agent
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_agent_chat))

    return app


async def start_telegram_bot() -> None:
    """Start Telegram long-polling in background if token is configured."""
    global _bot_app, _bot_task

    if not settings.telegram_bot_token:
        logger.info("TELEGRAM_BOT_TOKEN not configured in .env. Telegram bot is idle.")
        return

    logger.info("Initializing Telegram bot with long-polling...")
    try:
        _bot_app = create_telegram_app()
        await _bot_app.initialize()
        await setup_bot_commands(_bot_app)
        await _bot_app.start()

        # Run updater in background
        if _bot_app.updater:
            _bot_task = asyncio.create_task(_bot_app.updater.start_polling())
            logger.info("Telegram bot long-polling started successfully.")
    except Exception as e:
        logger.error("Failed to start Telegram bot: %s", e)


async def stop_telegram_bot() -> None:
    """Graceful shutdown of Telegram bot."""
    global _bot_app, _bot_task

    if _bot_app:
        try:
            logger.info("Stopping Telegram bot...")
            if _bot_app.updater and _bot_app.updater.running:
                await _bot_app.updater.stop()
            await _bot_app.stop()
            await _bot_app.shutdown()
            logger.info("Telegram bot stopped.")
        except Exception as e:
            logger.error("Error stopping Telegram bot: %s", e)

    if _bot_task and not _bot_task.done():
        _bot_task.cancel()
