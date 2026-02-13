"""
🤖🧠 JARVIS PERSONAL AI AGENT — Your Ultimate AI That Never Says No
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

JARVIS is your personal AI agent that can:
• Research ANY topic in seconds (news, crypto, stocks, tech, anything)
• Execute tasks autonomously (set reminders, track prices, manage money)
• Write code, generate images, create documents
• Monitor markets 24/7 and alert you on opportunities
• Personal assistant: weather, calendar, notes, todo lists
• Financial advisor: analyze investments, suggest strategies
• Learning assistant: explain any concept, solve math, translate
• Creative partner: write content, brainstorm ideas, plan projects

100% FREE — Powered by Groq + Gemini
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("JARVIS-AGENT")

# ═══════════════════════════════════════════════════════════
#  🧠 PERSONAL MEMORY + CONTEXT
# ═══════════════════════════════════════════════════════════

AGENT_MEMORY_FILE = Path("jarvis_agent_memory.json")
REMINDERS_FILE = Path("jarvis_reminders.json")
NOTES_FILE = Path("jarvis_notes.json")
TASKS_FILE = Path("jarvis_tasks.json")


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}


def _save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ═══════════════════════════════════════════════════════════
#  📝 PERSONAL NOTES SYSTEM
# ═══════════════════════════════════════════════════════════

def save_note(chat_id: int, title: str, content: str) -> dict:
    """Save a personal note."""
    notes = _load_json(NOTES_FILE)
    uid = str(chat_id)
    if uid not in notes:
        notes[uid] = []

    note = {
        "id": f"N{int(time.time())}",
        "title": title,
        "content": content,
        "created": datetime.now().isoformat(),
        "tags": _extract_tags(content),
    }
    notes[uid].append(note)
    _save_json(NOTES_FILE, notes)
    return note


def get_notes(chat_id: int, search: str = None) -> list:
    """Get user's notes, optionally filtered by search."""
    notes = _load_json(NOTES_FILE)
    user_notes = notes.get(str(chat_id), [])
    if search:
        search_lower = search.lower()
        user_notes = [n for n in user_notes
                      if search_lower in n.get("title", "").lower()
                      or search_lower in n.get("content", "").lower()]
    return user_notes[-20:]  # Last 20


def delete_note(chat_id: int, note_id: str) -> bool:
    notes = _load_json(NOTES_FILE)
    uid = str(chat_id)
    if uid in notes:
        notes[uid] = [n for n in notes[uid] if n.get("id") != note_id]
        _save_json(NOTES_FILE, notes)
        return True
    return False


# ═══════════════════════════════════════════════════════════
#  ⏰ REMINDER SYSTEM
# ═══════════════════════════════════════════════════════════

_reminder_callback = None
_reminder_running = False


def set_reminder_callback(callback):
    """Set callback: callback(chat_id, message)"""
    global _reminder_callback
    _reminder_callback = callback


def add_reminder(chat_id: int, text: str, minutes: int = 0, 
                 hours: int = 0, at_time: str = None) -> dict:
    """Add a reminder."""
    reminders = _load_json(REMINDERS_FILE)
    uid = str(chat_id)
    if uid not in reminders:
        reminders[uid] = []

    if at_time:
        # Parse specific time like "14:30" or "2:30 PM"
        try:
            today = datetime.now().date()
            remind_at = datetime.strptime(f"{today} {at_time}", "%Y-%m-%d %H:%M")
            if remind_at < datetime.now():
                remind_at += timedelta(days=1)  # Next day
        except Exception:
            remind_at = datetime.now() + timedelta(minutes=30)
    else:
        total_minutes = minutes + (hours * 60)
        if total_minutes <= 0:
            total_minutes = 30
        remind_at = datetime.now() + timedelta(minutes=total_minutes)

    reminder = {
        "id": f"R{int(time.time())}",
        "text": text,
        "remind_at": remind_at.isoformat(),
        "created": datetime.now().isoformat(),
        "status": "pending",
    }
    reminders[uid].append(reminder)
    _save_json(REMINDERS_FILE, reminders)

    return {
        "success": True,
        "reminder": reminder,
        "remind_at": remind_at.strftime("%I:%M %p, %d %b"),
    }


def get_reminders(chat_id: int) -> list:
    reminders = _load_json(REMINDERS_FILE)
    return [r for r in reminders.get(str(chat_id), []) if r.get("status") == "pending"]


def start_reminder_engine():
    """Start background reminder checker."""
    global _reminder_running
    if _reminder_running:
        return
    _reminder_running = True
    t = threading.Thread(target=_reminder_loop, daemon=True)
    t.start()
    logger.info("[AGENT] ⏰ Reminder engine STARTED")


def _reminder_loop():
    while _reminder_running:
        try:
            reminders = _load_json(REMINDERS_FILE)
            now = datetime.now()
            changed = False

            for uid, user_reminders in reminders.items():
                for r in user_reminders:
                    if r.get("status") != "pending":
                        continue
                    remind_at = datetime.fromisoformat(r["remind_at"])
                    if now >= remind_at:
                        r["status"] = "fired"
                        changed = True
                        if _reminder_callback:
                            _reminder_callback(int(uid),
                                f"⏰🔔 *REMINDER!*\n\n"
                                f"📝 {r['text']}\n\n"
                                f"_Set at {r['created'][:16]}_"
                            )

            if changed:
                _save_json(REMINDERS_FILE, reminders)
        except Exception as e:
            logger.error(f"Reminder loop error: {e}")

        time.sleep(30)  # Check every 30 seconds


# ═══════════════════════════════════════════════════════════
#  ✅ TODO / TASK MANAGER
# ═══════════════════════════════════════════════════════════

def add_task(chat_id: int, task: str, priority: str = "medium") -> dict:
    """Add a task to user's todo list."""
    tasks = _load_json(TASKS_FILE)
    uid = str(chat_id)
    if uid not in tasks:
        tasks[uid] = []

    task_item = {
        "id": f"T{int(time.time())}",
        "task": task,
        "priority": priority,  # high, medium, low
        "status": "pending",
        "created": datetime.now().isoformat(),
    }
    tasks[uid].append(task_item)
    _save_json(TASKS_FILE, tasks)
    return task_item


def get_tasks(chat_id: int) -> list:
    tasks = _load_json(TASKS_FILE)
    return [t for t in tasks.get(str(chat_id), []) if t.get("status") != "done"]


def complete_task(chat_id: int, task_id: str) -> bool:
    tasks = _load_json(TASKS_FILE)
    uid = str(chat_id)
    for t in tasks.get(uid, []):
        if t.get("id") == task_id:
            t["status"] = "done"
            t["completed_at"] = datetime.now().isoformat()
            _save_json(TASKS_FILE, tasks)
            return True
    return False


# ═══════════════════════════════════════════════════════════
#  🌐 RESEARCH ENGINE — Multi-Source
# ═══════════════════════════════════════════════════════════

def research_topic(query: str) -> dict:
    """Research any topic from multiple free sources."""
    results = {
        "query": query,
        "sources": [],
        "summary": "",
    }

    import requests

    # Source 1: Wikipedia
    try:
        resp = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_"),
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results["sources"].append({
                "source": "Wikipedia",
                "title": data.get("title", ""),
                "summary": data.get("extract", "")[:500],
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            })
    except Exception:
        pass

    # Source 2: News (NewsAPI)
    try:
        news_key = os.environ.get("NEWS_API_KEY", "")
        if news_key:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "pageSize": 5, "sortBy": "publishedAt", "apiKey": news_key},
                timeout=10,
            )
            if resp.status_code == 200:
                for article in resp.json().get("articles", [])[:3]:
                    results["sources"].append({
                        "source": "News",
                        "title": article.get("title", ""),
                        "summary": article.get("description", "")[:300],
                        "url": article.get("url", ""),
                        "published": article.get("publishedAt", "")[:10],
                    })
    except Exception:
        pass

    # Source 3: CoinGecko (for crypto queries)
    crypto_keywords = ["bitcoin", "crypto", "eth", "solana", "token", "coin", "defi", "nft"]
    if any(kw in query.lower() for kw in crypto_keywords):
        try:
            resp = requests.get(
                f"https://api.coingecko.com/api/v3/search",
                params={"query": query},
                timeout=10,
            )
            if resp.status_code == 200:
                coins = resp.json().get("coins", [])[:3]
                for coin in coins:
                    results["sources"].append({
                        "source": "CoinGecko",
                        "title": coin.get("name", ""),
                        "summary": f"Symbol: {coin.get('symbol', '').upper()}, "
                                   f"Market Cap Rank: #{coin.get('market_cap_rank', 'N/A')}",
                        "url": f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                    })
        except Exception:
            pass

    # Source 4: DuckDuckGo Instant Answers
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                results["sources"].append({
                    "source": "DuckDuckGo",
                    "title": data.get("Heading", query),
                    "summary": abstract[:500],
                    "url": data.get("AbstractURL", ""),
                })
    except Exception:
        pass

    return results


def format_research(results: dict) -> str:
    """Format research results for Telegram."""
    if not results["sources"]:
        return f"🔍 '{results['query']}' ke baare mein koi result nahi mila."

    msg = (
        f"🔍🧠 *JARVIS RESEARCH — {results['query'][:50]}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for i, src in enumerate(results["sources"][:6], 1):
        source_emoji = {"Wikipedia": "📚", "News": "📰", "CoinGecko": "🪙", "DuckDuckGo": "🦆"}.get(src["source"], "🔗")
        msg += (
            f"{source_emoji} *{src['source']}:* {src['title'][:60]}\n"
            f"  {src['summary'][:200]}\n"
        )
        if src.get("url"):
            msg += f"  🔗 [Read More]({src['url']})\n"
        msg += "\n"

    msg += f"_🤖 JARVIS ne {len(results['sources'])} sources se research kiya_"
    return msg


# ═══════════════════════════════════════════════════════════
#  🌤️ WEATHER + UTILITIES
# ═══════════════════════════════════════════════════════════

def get_weather(city: str = "Delhi") -> str:
    """Get weather for any city."""
    try:
        import requests
        key = os.environ.get("OPENWEATHER_API_KEY", "")
        if not key:
            return "Weather API key not set."

        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": key, "units": "metric"},
            timeout=10,
        )
        if resp.status_code == 200:
            d = resp.json()
            temp = d["main"]["temp"]
            feels = d["main"]["feels_like"]
            desc = d["weather"][0]["description"].title()
            humidity = d["main"]["humidity"]
            wind = d["wind"]["speed"]

            weather_emoji = {
                "clear": "☀️", "clouds": "☁️", "rain": "🌧️",
                "drizzle": "🌦️", "thunderstorm": "⛈️", "snow": "❄️",
                "mist": "🌫️", "fog": "🌫️", "haze": "🌫️",
            }
            main_weather = d["weather"][0]["main"].lower()
            emoji = weather_emoji.get(main_weather, "🌤️")

            return (
                f"{emoji} *Weather — {city.title()}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌡️ Temp: *{temp}°C* (Feels like {feels}°C)\n"
                f"☁️ Condition: {desc}\n"
                f"💧 Humidity: {humidity}%\n"
                f"💨 Wind: {wind} m/s\n"
            )
        return f"Weather data not available for {city}"
    except Exception as e:
        return f"Weather error: {e}"


def calculate(expression: str) -> str:
    """Safe math calculator."""
    try:
        # Allow only safe math operations
        allowed = set("0123456789+-*/().%^ ")
        if not all(c in allowed for c in expression.replace("**", "^").replace("^", "**")):
            return "Invalid expression"

        result = eval(expression, {"__builtins__": {}}, {})
        return f"🧮 {expression} = *{result:,}*" if isinstance(result, (int, float)) else str(result)
    except Exception as e:
        return f"Calculation error: {e}"


def translate_text(text: str, target_lang: str = "hi") -> str:
    """Translate text using free API."""
    try:
        import requests
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:500], "langpair": f"en|{target_lang}"},
            timeout=10,
        )
        if resp.status_code == 200:
            translated = resp.json().get("responseData", {}).get("translatedText", "")
            return f"🌐 *Translation:*\n\n{translated}" if translated else "Translation failed"
    except Exception:
        pass
    return "Translation service unavailable"


# ═══════════════════════════════════════════════════════════
#  🤖 AGENT BRAIN — Intent Detection + Action
# ═══════════════════════════════════════════════════════════

def detect_agent_intent(text: str) -> dict:
    """
    Detect what the user wants JARVIS to do.
    Returns: {"intent": str, "params": dict}
    """
    text_lower = text.lower().strip()

    # Reminder patterns
    reminder_keywords = ["remind", "yaad", "reminder", "alert me", "batana", "bata dena"]
    if any(kw in text_lower for kw in reminder_keywords):
        # Extract time
        minutes = 0
        if "minute" in text_lower or "min" in text_lower:
            import re
            m = re.search(r'(\d+)\s*(?:min|minute)', text_lower)
            minutes = int(m.group(1)) if m else 30
        elif "hour" in text_lower or "ghante" in text_lower:
            import re
            m = re.search(r'(\d+)\s*(?:hour|ghante|hr)', text_lower)
            minutes = int(m.group(1)) * 60 if m else 60
        else:
            minutes = 30

        return {"intent": "reminder", "params": {"text": text, "minutes": minutes}}

    # Note patterns
    note_keywords = ["note", "save", "likh", "yaad rakh", "remember"]
    if any(kw in text_lower for kw in note_keywords):
        return {"intent": "note", "params": {"content": text}}

    # Todo patterns
    todo_keywords = ["todo", "task", "kaam", "add task", "karna hai"]
    if any(kw in text_lower for kw in todo_keywords):
        return {"intent": "task", "params": {"task": text}}

    # Weather patterns
    weather_keywords = ["weather", "mausam", "temperature", "barish", "rain", "garmi"]
    if any(kw in text_lower for kw in weather_keywords):
        # Extract city
        city = "Delhi"
        cities = ["mumbai", "delhi", "bangalore", "chennai", "kolkata", "hyderabad",
                  "pune", "jaipur", "lucknow", "ahmedabad", "new york", "london"]
        for c in cities:
            if c in text_lower:
                city = c.title()
                break
        return {"intent": "weather", "params": {"city": city}}

    # Calculator
    calc_keywords = ["calculate", "calc", "kitna", "=", "plus", "minus", "multiply"]
    if any(kw in text_lower for kw in calc_keywords):
        import re
        expr = re.sub(r'[a-zA-Z\s]', '', text).strip()
        return {"intent": "calculate", "params": {"expression": expr or text}}

    # Research
    research_keywords = ["research", "search", "find", "what is", "kya hai", "batao",
                         "explain", "samjhao", "meaning", "matlab"]
    if any(kw in text_lower for kw in research_keywords):
        return {"intent": "research", "params": {"query": text}}

    # Default: let AI handle it
    return {"intent": "ai_chat", "params": {"message": text}}


def execute_agent_action(chat_id: int, intent: dict) -> str:
    """Execute the detected agent action."""
    action = intent["intent"]
    params = intent["params"]

    if action == "reminder":
        result = add_reminder(chat_id, params["text"], minutes=params.get("minutes", 30))
        if result.get("success"):
            return f"⏰ *Reminder Set!*\n\n📝 {params['text']}\n⏰ {result['remind_at']}"
        return "❌ Reminder set nahi ho paya"

    elif action == "note":
        note = save_note(chat_id, "Quick Note", params["content"])
        return f"📝 *Note Saved!* (ID: {note['id']})\n\n{params['content'][:200]}"

    elif action == "task":
        task = add_task(chat_id, params["task"])
        return f"✅ *Task Added!*\n\n📋 {params['task']}\n🆔 {task['id']}"

    elif action == "weather":
        return get_weather(params.get("city", "Delhi"))

    elif action == "calculate":
        return calculate(params.get("expression", ""))

    elif action == "research":
        results = research_topic(params["query"])
        return format_research(results)

    return ""  # Let AI chat handle it


# ═══════════════════════════════════════════════════════════
#  📱 FORMAT FUNCTIONS
# ═══════════════════════════════════════════════════════════

def format_notes(chat_id: int) -> str:
    """Format user's notes."""
    notes = get_notes(chat_id)
    if not notes:
        return "📝 Koi notes nahi hain.\n\nNote save karo: `/note Your note text here`"

    msg = "📝💡 *JARVIS NOTES*\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for n in notes[-10:]:
        msg += f"• *{n['title']}* — {n['content'][:80]}\n  _ID: {n['id']} | {n['created'][:10]}_\n\n"
    return msg


def format_tasks(chat_id: int) -> str:
    """Format user's tasks."""
    tasks = get_tasks(chat_id)
    if not tasks:
        return "✅ Koi pending tasks nahi hain! 🎉\n\nTask add karo: `/task Your task here`"

    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    msg = "✅📋 *JARVIS TODO LIST*\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for t in tasks:
        emoji = priority_emoji.get(t.get("priority", "medium"), "🟡")
        msg += f"{emoji} {t['task']}\n  _ID: {t['id']} | {t['created'][:10]}_\n\n"
    msg += "_Complete: `/done TASK_ID`_"
    return msg


def format_reminders(chat_id: int) -> str:
    """Format user's reminders."""
    rems = get_reminders(chat_id)
    if not rems:
        return "⏰ Koi pending reminders nahi hain.\n\nSet karo: `/remind 30 min mein meeting hai`"

    msg = "⏰🔔 *JARVIS REMINDERS*\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for r in rems:
        msg += f"• {r['text']}\n  ⏰ {r['remind_at'][:16]}\n\n"
    return msg


def format_agent_dashboard(chat_id: int) -> str:
    """Format complete agent dashboard."""
    notes_count = len(get_notes(chat_id))
    tasks_count = len(get_tasks(chat_id))
    reminders_count = len(get_reminders(chat_id))

    return (
        f"🤖🧠 *JARVIS PERSONAL AI AGENT* 🧠🤖\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Main hoon aapka personal AI — jo kabhi na nahi bole! 🚀\n\n"
        f"📊 *YOUR DATA:*\n"
        f"  📝 Notes: {notes_count}\n"
        f"  ✅ Tasks: {tasks_count}\n"
        f"  ⏰ Reminders: {reminders_count}\n\n"
        f"🎯 *WHAT I CAN DO:*\n"
        f"  📝 `/note` — Notes save karo\n"
        f"  ✅ `/task` — Todo list manage karo\n"
        f"  ⏰ `/remind` — Reminders set karo\n"
        f"  🔍 `/research` — Kuch bhi research karo\n"
        f"  🌤️ `/weather` — Weather check karo\n"
        f"  🧮 `/calc` — Calculate karo\n"
        f"  💰 `/deposit` — Paise deposit karo (UPI)\n"
        f"  🤖 `/autoinvest` — Auto crypto invest\n"
        f"  📊 `/portfolio` — Portfolio dekho\n"
        f"  🏦 `/withdraw` — Bank mein withdraw\n"
        f"  👛 `/wallet` — Wallet dashboard\n\n"
        f"💡 Ya bas baat karo — main samajh jaunga! 😊\n\n"
        f"_🤖 JARVIS — Your AI, Your Rules, Always FREE_"
    )


def _extract_tags(text: str) -> list:
    """Extract hashtags and keywords from text."""
    import re
    tags = re.findall(r'#(\w+)', text)
    return tags[:5]


# ═══════════════════════════════════════════════════════════
#  MODULE EXPORTS
# ═══════════════════════════════════════════════════════════

AGENT_AVAILABLE = True

__all__ = [
    'AGENT_AVAILABLE',
    'save_note', 'get_notes', 'delete_note',
    'add_reminder', 'get_reminders', 'set_reminder_callback', 'start_reminder_engine',
    'add_task', 'get_tasks', 'complete_task',
    'research_topic', 'format_research',
    'get_weather', 'calculate', 'translate_text',
    'detect_agent_intent', 'execute_agent_action',
    'format_notes', 'format_tasks', 'format_reminders', 'format_agent_dashboard',
]

logger.info("[AGENT] 🤖🧠 JARVIS Personal AI Agent loaded — Never says NO!")
