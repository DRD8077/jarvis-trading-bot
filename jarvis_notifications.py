"""
📱 JARVIS Notifications — Telegram Push Notifications
════════════════════════════════════════════════════════
- Push high-confidence signals (BUY/SELL > 80%)
- Price alerts
- Portfolio updates
- Admin notifications
- Broadcast messages
"""

import os
import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("jarvis-notify")
IST = timezone(timedelta(hours=5, minutes=30))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Subscriber store (chat_id → preferences)
_subscribers: Dict[str, Dict] = {}
_notification_log: List[Dict] = []
MAX_LOG = 200


# ═══════════════════════════════════════════════════════════
#  TELEGRAM SEND
# ═══════════════════════════════════════════════════════════
async def _send_telegram(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Send a message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping notification")
        return False
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{TELEGRAM_API}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
                if not data.get("ok"):
                    logger.error(f"Telegram send failed: {data}")
                    return False
                return True
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False


async def send_to_all(text: str, filter_pref: str = None) -> Dict:
    """Broadcast to all subscribers. Returns {sent, total}."""
    sent = 0
    total = len(_subscribers)
    # Also send to admin if no subscribers
    admin_id = os.getenv("ADMIN_CHAT_ID", os.getenv("OWNER_CHAT_ID", ""))
    if not _subscribers and admin_id:
        ok = await _send_telegram(admin_id, text)
        return {"sent": 1 if ok else 0, "total": 1}
    for chat_id, prefs in _subscribers.items():
        if filter_pref and not prefs.get(filter_pref, True):
            continue
        ok = await _send_telegram(chat_id, text)
        if ok:
            sent += 1
    return {"sent": sent, "total": total}


# ═══════════════════════════════════════════════════════════
#  SIGNAL NOTIFICATIONS
# ═══════════════════════════════════════════════════════════
async def notify_signal(signal: Dict) -> int:
    """Push high-confidence signal to subscribers."""
    confidence = signal.get("confidence", 0)
    if confidence < 75:
        return 0

    action = signal.get("action", "HOLD")
    symbol = signal.get("symbol", "???")
    price = signal.get("price", "N/A")
    source = signal.get("source", "JARVIS AI")

    # Confidence emoji
    if confidence >= 90:
        conf_emoji = "🔥🔥🔥"
    elif confidence >= 80:
        conf_emoji = "🔥🔥"
    else:
        conf_emoji = "🔥"

    # Action emoji
    action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(action, "⚪")

    text = (
        f"{action_emoji} <b>{action} Signal</b> {conf_emoji}\n\n"
        f"📊 <b>{symbol}</b>\n"
        f"💰 Price: <code>{price}</code>\n"
        f"📈 Confidence: <b>{confidence}%</b>\n"
        f"🤖 Source: {source}\n"
        f"🕐 {datetime.now(IST).strftime('%I:%M %p IST')}\n\n"
        f"⚡ <i>JARVIS AI Signal Engine</i>"
    )

    sent = await send_to_all(text, filter_pref="signals")
    _log("signal", symbol, f"{action} {confidence}%", sent)
    return sent


# ═══════════════════════════════════════════════════════════
#  PRICE ALERTS
# ═══════════════════════════════════════════════════════════
async def notify_price_alert(chat_id: str, symbol: str, target_price: float,
                              current_price: float, direction: str) -> bool:
    """Send price alert to specific user."""
    arrow = "⬆️" if direction == "above" else "⬇️"
    text = (
        f"🔔 <b>Price Alert Triggered!</b>\n\n"
        f"📊 <b>{symbol}</b>\n"
        f"{arrow} Target: <code>${target_price:,.4f}</code>\n"
        f"💰 Current: <code>${current_price:,.4f}</code>\n"
        f"🕐 {datetime.now(IST).strftime('%I:%M %p IST')}"
    )
    ok = await _send_telegram(chat_id, text)
    _log("price_alert", symbol, f"{direction} ${target_price}", 1 if ok else 0)
    return ok


# ═══════════════════════════════════════════════════════════
#  PORTFOLIO NOTIFICATIONS
# ═══════════════════════════════════════════════════════════
async def notify_portfolio_update(chat_id: str, pnl: float, top_gains: List[Dict],
                                   top_losses: List[Dict]) -> bool:
    """Send daily portfolio summary."""
    pnl_emoji = "📈" if pnl >= 0 else "📉"
    pnl_sign = "+" if pnl >= 0 else ""

    gains_text = "\n".join([f"  🟢 {g['symbol']}: +{g['pnl']:.2f}%" for g in top_gains[:3]]) or "  None"
    losses_text = "\n".join([f"  🔴 {l['symbol']}: {l['pnl']:.2f}%" for l in top_losses[:3]]) or "  None"

    text = (
        f"{pnl_emoji} <b>Daily Portfolio Summary</b>\n\n"
        f"💰 PnL: <b>{pnl_sign}{pnl:.2f}%</b>\n\n"
        f"<b>Top Gainers:</b>\n{gains_text}\n\n"
        f"<b>Top Losers:</b>\n{losses_text}\n\n"
        f"🕐 {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}"
    )
    return await _send_telegram(chat_id, text)


# ═══════════════════════════════════════════════════════════
#  ADMIN NOTIFICATIONS
# ═══════════════════════════════════════════════════════════
async def notify_admin(message: str, severity: str = "info") -> bool:
    """Send notification to admin (owner)."""
    admin_id = os.getenv("ADMIN_CHAT_ID", os.getenv("OWNER_CHAT_ID", ""))
    if not admin_id:
        return False

    emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🚨", "critical": "🔴"}.get(severity, "ℹ️")
    text = (
        f"{emoji} <b>Admin Alert</b> [{severity.upper()}]\n\n"
        f"{message}\n\n"
        f"🕐 {datetime.now(IST).strftime('%I:%M %p IST')}"
    )
    return await _send_telegram(admin_id, text)


async def broadcast_message(text: str) -> int:
    """Broadcast admin message to all subscribers."""
    msg = f"📢 <b>JARVIS Broadcast</b>\n\n{text}"
    sent = await send_to_all(msg)
    _log("broadcast", "all", text[:50], sent)
    return sent


# ═══════════════════════════════════════════════════════════
#  SUBSCRIBER MANAGEMENT
# ═══════════════════════════════════════════════════════════
def subscribe(chat_id: str, preferences: Dict = None) -> Dict:
    """Subscribe to notifications."""
    prefs = preferences or {"signals": True, "alerts": True, "portfolio": True, "broadcast": True}
    _subscribers[str(chat_id)] = prefs
    return prefs


def unsubscribe(chat_id: str) -> bool:
    """Unsubscribe from notifications."""
    return _subscribers.pop(str(chat_id), None) is not None


def update_preferences(chat_id: str, preferences: Dict) -> Dict:
    """Update notification preferences."""
    if str(chat_id) in _subscribers:
        _subscribers[str(chat_id)].update(preferences)
        return _subscribers[str(chat_id)]
    return subscribe(chat_id, preferences)


def get_subscribers() -> Dict[str, Dict]:
    """Get all subscribers."""
    return _subscribers.copy()


# ═══════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════
def _log(ntype: str, target: str, details: str, sent: int):
    """Log notification."""
    entry = {
        "type": ntype,
        "target": target,
        "details": details,
        "sent_count": sent,
        "timestamp": datetime.now(IST).isoformat(),
    }
    _notification_log.append(entry)
    if len(_notification_log) > MAX_LOG:
        _notification_log.pop(0)


def get_notification_stats() -> Dict:
    """Get notification statistics."""
    return {
        "total_subscribers": len(_subscribers),
        "total_sent": len(_notification_log),
        "recent": _notification_log[-10:],
        "by_type": {},
        "bot_configured": bool(TELEGRAM_BOT_TOKEN),
    }


# Alias for server compatibility
send_signal_alert = notify_signal

NOTIFICATIONS_AVAILABLE = True
logger.info("📱 Telegram notification engine loaded")
