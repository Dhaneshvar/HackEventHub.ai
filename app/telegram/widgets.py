"""Telegram Widgets & Inline Keyboards with compact callback_data (<64 bytes)."""

from __future__ import annotations

import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Interests, Item, PriceStatus, Tool


def escape_html(text: str) -> str:
    """Escape special HTML characters for Telegram HTML mode."""
    if not text:
        return ""
    return html.escape(str(text))


# ─── Compact Callback Protocol (<64 bytes) ──────────────────────────────────
# Format: <category>:<action>:<payload>
# Categories:
#   i: item -> s: save, h: hide, d: details
#   t: tool -> g: toggle, r: run
#   p: provider -> s: set active
#   f: filter/pref -> o: online, f: free, r: relevance
#   m: menu / pagination -> p: page


def build_item_card_markup(item_id: int, url: str = "", is_saved: bool = False) -> InlineKeyboardMarkup:
    """Build compact inline keyboard for an opportunity card."""
    buttons = []
    first_row = []

    if url:
        first_row.append(InlineKeyboardButton("🔗 Open", url=url))

    first_row.append(InlineKeyboardButton("ℹ️ Details", callback_data=f"i:d:{item_id}"))

    if not is_saved:
        first_row.append(InlineKeyboardButton("⭐ Save", callback_data=f"i:s:{item_id}"))
    else:
        first_row.append(InlineKeyboardButton("✅ Saved", callback_data=f"i:s:{item_id}"))

    first_row.append(InlineKeyboardButton("🚫 Hide", callback_data=f"i:h:{item_id}"))

    buttons.append(first_row)
    return InlineKeyboardMarkup(buttons)


def format_item_card(item: Item, show_full: bool = False) -> str:
    """Format an opportunity item as a clean HTML Telegram card."""
    title = escape_html(item.title)
    city = escape_html(item.city) if item.city else ""
    loc = "🌐 Online" if item.is_online else (f"📍 {city}" if city else "📍 In-person")
    price = (
        "🆓 Free"
        if item.price_status in ("free", PriceStatus.FREE)
        else ("💰 Paid" if item.price_status in ("paid", PriceStatus.PAID) else "❓ Price TBD")
    )
    relevance = f"⭐ {int(item.relevance_score * 100)}% match"

    dates = ""
    if item.start_date:
        dates = f"\n📅 {item.start_date.strftime('%b %d, %Y')}"
        if item.end_date and item.end_date != item.start_date:
            dates += f" – {item.end_date.strftime('%b %d, %Y')}"

    text = f"<b>{title}</b>\n{loc} • {price} • {relevance}{dates}"

    if item.relevance_reason:
        text += f"\n<i>💡 {escape_html(item.relevance_reason)}</i>"

    if show_full and item.description_snippet:
        text += f"\n\n{escape_html(item.description_snippet[:400])}..."

    if item.organizer:
        text += f"\n\n👤 <b>Organizer:</b> {escape_html(item.organizer)}"

    return text


def build_pagination_markup(page: int, total_pages: int, prefix: str) -> list[InlineKeyboardButton]:
    """Build Prev / Next pagination buttons."""
    row = []
    if page > 1:
        row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"m:{prefix}:{page - 1}"))
    row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        row.append(InlineKeyboardButton("Next ▶️", callback_data=f"m:{prefix}:{page + 1}"))
    return row


def build_tools_markup(tools: list[Tool]) -> InlineKeyboardMarkup:
    """Build inline buttons for managing tools in chat."""
    keyboard = []
    for t in tools[:8]:  # Keep clean in telegram
        status_icon = "🟢" if t.enabled else "⚪"
        row = [
            InlineKeyboardButton(
                f"{status_icon} {t.name[:18] or t.url[:18]}",
                callback_data=f"t:g:{t.id}",
            ),
            InlineKeyboardButton("▶️ Run", callback_data=f"t:r:{t.id}"),
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def build_providers_markup(current_active: str) -> InlineKeyboardMarkup:
    """Build buttons to switch the active LLM provider."""
    providers = [
        ("ollama", "🦙 Ollama (Local)"),
        ("azure", "☁️ Azure OpenAI"),
        ("athena", "🏛️ Unisys Athena"),
    ]
    buttons = []
    for code, label in providers:
        prefix = "✅ " if code == current_active else ""
        buttons.append([InlineKeyboardButton(f"{prefix}{label}", callback_data=f"p:s:{code}")])
    return InlineKeyboardMarkup(buttons)


def build_prefs_markup(interests: Interests) -> InlineKeyboardMarkup:
    """Build preference toggle buttons."""
    free_icon = "✅" if interests.free_only else "❌"
    online_icon = "✅" if interests.include_online else "❌"
    alerts_icon = "🔔" if interests.instant_alerts else "🔕"

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"Free Only: {free_icon}", callback_data="f:f:tog"),
                InlineKeyboardButton(f"Online Events: {online_icon}", callback_data="f:o:tog"),
            ],
            [
                InlineKeyboardButton(f"Instant Alerts: {alerts_icon}", callback_data="f:a:tog"),
            ],
        ]
    )


def build_main_menu_markup() -> InlineKeyboardMarkup:
    """Main dashboard menu button grid."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📅 Today", callback_data="cmd:today"),
                InlineKeyboardButton("⚡ Run Now", callback_data="cmd:now"),
            ],
            [
                InlineKeyboardButton("🗓️ This Week", callback_data="cmd:week"),
                InlineKeyboardButton("✨ What's New", callback_data="cmd:new"),
            ],
            [
                InlineKeyboardButton("🌐 Tools", callback_data="cmd:tools"),
                InlineKeyboardButton("🧠 LLM Provider", callback_data="cmd:provider"),
            ],
            [
                InlineKeyboardButton("⚙️ Preferences", callback_data="cmd:prefs"),
                InlineKeyboardButton("📊 System Status", callback_data="cmd:status"),
            ],
        ]
    )
