"""
🧠🔱 J.A.R.V.I.S. SPOC — Single Point of Contact
═══════════════════════════════════════════════════════════════
JARVIS is the BRAIN of the entire project ecosystem.
Reports DIRECTLY to: DEEPAK KUMAR (Boss/Owner)

Monitors:
  1. All Python engines (30+ modules)
  2. Background threads (alert engine, gem scanner, rocket scanner, monitor)
  3. API health (Telegram, DexScreener, CoinDCX, pump.fun, CoinGecko, NSE)
  4. System resources (CPU, Memory, Disk, Uptime)
  5. Error tracking across all modules
  6. User activity & command stats
  7. Phantom Wallet connections
  8. ML model performance

Reports to Deepak Kumar:
  - System health dashboard
  - Daily briefing
  - Critical error alerts
  - Module status (alive/dead/degraded)
  - API response times
  - User engagement stats

Author: JARVIS AI — for Boss Deepak Kumar
"""

import os
import sys
import time
import logging
import threading
import traceback
import importlib
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger("jarvis_spoc")

# ═══════════════════════════════════════════════════════════
#  BOSS CONFIGURATION
# ═══════════════════════════════════════════════════════════

BOSS_NAME = "Deepak Kumar"
BOSS_CHAT_ID = int(os.environ.get("TEST_CHAT_ID", "0"))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════
#  PROJECT MODULE REGISTRY — Every engine JARVIS monitors
# ═══════════════════════════════════════════════════════════

PROJECT_MODULES = {
    # Core Bot
    "telegram_bot": {"name": "Telegram Bot", "icon": "🤖", "critical": True, "type": "core"},
    "jarvis_ai": {"name": "JARVIS AI Brain", "icon": "🧠", "critical": True, "type": "core"},
    "jarvis_monitor": {"name": "JARVIS Monitor", "icon": "🔔", "critical": True, "type": "core"},
    "voice_engine": {"name": "Voice Engine", "icon": "🎤", "critical": False, "type": "core"},
    "ai_chat": {"name": "AI Chat Engine", "icon": "💬", "critical": False, "type": "core"},
    "admin_panel": {"name": "Admin Panel", "icon": "👑", "critical": False, "type": "core"},

    # Stock Market
    "indian_stock_super_engine": {"name": "🇮🇳 Indian Super Engine (ATM/OTM/Holidays)", "icon": "🔱", "critical": True, "type": "stock"},
    "stock_data_fetcher": {"name": "Stock Data Fetcher", "icon": "📊", "critical": True, "type": "stock"},
    "live_index_engine": {"name": "Live Index Engine", "icon": "📈", "critical": True, "type": "stock"},
    "options_engine": {"name": "Options Engine", "icon": "⚡", "critical": False, "type": "stock"},
    "buy_sell_engine": {"name": "Buy/Sell Engine", "icon": "💰", "critical": True, "type": "stock"},
    "candle_analyzer": {"name": "Candle Analyzer", "icon": "🕯️", "critical": False, "type": "stock"},

    # Crypto
    "crypto_engine": {"name": "Crypto Engine", "icon": "🪙", "critical": True, "type": "crypto"},
    "coindcx_engine": {"name": "CoinDCX Engine", "icon": "🔵", "critical": True, "type": "crypto"},
    "crypto_intelligence": {"name": "Crypto Intelligence", "icon": "🔍", "critical": True, "type": "crypto"},
    "web3_rocket_scanner": {"name": "Rocket Scanner", "icon": "🚀", "critical": True, "type": "crypto"},
    "rug_detector": {"name": "Rug Detector", "icon": "🛡️", "critical": True, "type": "crypto"},
    "whale_alert": {"name": "Whale Alert", "icon": "🐋", "critical": False, "type": "crypto"},
    "portfolio_tracker": {"name": "Portfolio Tracker", "icon": "📂", "critical": False, "type": "crypto"},

    # ML/AI
    "ml_pipeline": {"name": "ML Pipeline", "icon": "🤖", "critical": False, "type": "ml"},
    "ml_predictor": {"name": "ML Predictor", "icon": "🔮", "critical": False, "type": "ml"},
    "sentiment_engine": {"name": "Sentiment Engine", "icon": "📰", "critical": False, "type": "ml"},
    "market_regime": {"name": "Market Regime", "icon": "🌊", "critical": False, "type": "ml"},
    "risk_manager": {"name": "Risk Manager", "icon": "⚠️", "critical": False, "type": "ml"},

    # Infra
    "sms_engine": {"name": "SMS Engine", "icon": "📲", "critical": False, "type": "infra"},
    "scheduler": {"name": "Scheduler", "icon": "⏰", "critical": False, "type": "infra"},
    "alerter": {"name": "Alerter", "icon": "🔔", "critical": False, "type": "infra"},
    "global_candle_engine": {"name": "Global Candle Engine", "icon": "🌍", "critical": False, "type": "stock"},
    "global_market_analyzer": {"name": "Global Market Analyzer", "icon": "🌐", "critical": False, "type": "stock"},
    "data_store": {"name": "Data Store", "icon": "💾", "critical": False, "type": "infra"},

    # New
    "phantom_wallet": {"name": "Phantom Wallet", "icon": "👻", "critical": False, "type": "crypto"},
    "jarvis_market_brain": {"name": "Market Brain (Router)", "icon": "🧠", "critical": False, "type": "ml"},
    "index_data": {"name": "Index Data (250+ Features)", "icon": "📈", "critical": False, "type": "ml"},
}

# ═══════════════════════════════════════════════════════════
#  HEALTH CHECK APIs
# ═══════════════════════════════════════════════════════════

API_ENDPOINTS = {
    "Telegram": "https://api.telegram.org/bot{token}/getMe",
    "DexScreener": "https://api.dexscreener.com/latest/dex/search?q=SOL",
    "pump.fun": "https://frontend-api-v2.pump.fun/coins/trending",
    "CoinDCX": "https://api.coindcx.com/exchange/ticker",
}

# ═══════════════════════════════════════════════════════════
#  RUNTIME TRACKING
# ═══════════════════════════════════════════════════════════

_start_time = datetime.now()
_module_status: Dict[str, dict] = {}
_api_health: Dict[str, dict] = {}
_error_log: List[dict] = []
_command_stats: Dict[str, int] = defaultdict(int)
_thread_status: Dict[str, dict] = {}
_spoc_running = False
_spoc_thread = None
_daily_report_sent = False
_last_health_check = None

# ═══════════════════════════════════════════════════════════
#  MODULE HEALTH CHECK — Import & test each module
# ═══════════════════════════════════════════════════════════

def check_module_health() -> Dict[str, dict]:
    """Check if every module in the project can be imported and is functional."""
    global _module_status
    results = {}

    for mod_name, info in PROJECT_MODULES.items():
        status = {
            "name": info["name"],
            "icon": info["icon"],
            "type": info["type"],
            "critical": info["critical"],
            "status": "unknown",
            "error": None,
            "load_time_ms": 0,
        }

        start = time.time()
        try:
            mod = importlib.import_module(mod_name)
            elapsed = (time.time() - start) * 1000
            status["status"] = "alive"
            status["load_time_ms"] = round(elapsed, 1)

            # Check if module has key functions
            func_count = len([x for x in dir(mod) if callable(getattr(mod, x, None)) and not x.startswith("_")])
            status["functions"] = func_count

            # Get file size
            if hasattr(mod, "__file__") and mod.__file__:
                try:
                    fsize = os.path.getsize(mod.__file__)
                    status["file_size"] = fsize
                    status["lines"] = sum(1 for _ in open(mod.__file__))
                except:
                    pass

        except ImportError as e:
            status["status"] = "not_installed"
            status["error"] = str(e)[:100]
        except Exception as e:
            status["status"] = "error"
            status["error"] = str(e)[:100]

        results[mod_name] = status

    _module_status = results
    return results


def check_api_health(token: str = None) -> Dict[str, dict]:
    """Check health of all external APIs."""
    global _api_health
    results = {}

    bot_token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")

    for api_name, url_template in API_ENDPOINTS.items():
        url = url_template.format(token=bot_token) if "{token}" in url_template else url_template
        status = {"name": api_name, "status": "unknown", "response_ms": 0, "error": None}

        try:
            start = time.time()
            r = requests.get(url, timeout=10)
            elapsed = (time.time() - start) * 1000
            status["response_ms"] = round(elapsed, 1)

            if r.status_code == 200:
                status["status"] = "healthy"
            elif r.status_code == 429:
                status["status"] = "rate_limited"
            else:
                status["status"] = "degraded"
                status["error"] = f"HTTP {r.status_code}"
        except requests.Timeout:
            status["status"] = "timeout"
            status["error"] = "Request timed out"
        except Exception as e:
            status["status"] = "down"
            status["error"] = str(e)[:80]

        results[api_name] = status

    _api_health = results
    return results


def check_system_resources() -> dict:
    """Check system CPU, RAM, disk usage."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime_sec = (datetime.now() - _start_time).total_seconds()

        return {
            "cpu_percent": cpu,
            "ram_total_gb": round(ram.total / (1024**3), 1),
            "ram_used_gb": round(ram.used / (1024**3), 1),
            "ram_percent": ram.percent,
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "disk_used_gb": round(disk.used / (1024**3), 1),
            "disk_percent": round(disk.percent, 1),
            "bot_uptime_sec": int(uptime_sec),
            "bot_uptime_str": _format_uptime(uptime_sec),
            "python_version": sys.version.split()[0],
            "threads_active": threading.active_count(),
        }
    except Exception as e:
        return {"error": str(e), "cpu_percent": -1, "ram_percent": -1}


def check_background_threads() -> Dict[str, dict]:
    """Check status of all background threads."""
    global _thread_status
    results = {}

    # Map: actual thread name -> display name
    # These MUST match the names used in threading.Thread(name=...)
    expected_threads = {
        "AutoAlertEngine": "🔔 Auto-Alert Engine",
        "CryptoGemScanner": "🪙 Crypto Gem Scanner",
        "RocketScanner": "🚀 Rocket Scanner",
        "jarvis-monitor": "🔔 JARVIS Monitor",
        "keepalive-watchdog": "🏥 Keep-Alive Watchdog",
        "new-token-detector": "🆕 New Token Detector",
        "jarvis-spoc": "🧠 JARVIS SPOC",
        "MainSupervisor": "🛡️ Main Supervisor",
        "thread-supervisor": "🛡️ Thread Supervisor",
    }

    active_names = [t.name for t in threading.enumerate()]

    for thread_id, thread_name in expected_threads.items():
        is_alive = thread_id in active_names
        results[thread_id] = {
            "name": thread_name,
            "alive": is_alive,
            "status": "running" if is_alive else "stopped",
        }

    _thread_status = results
    return results


# ═══════════════════════════════════════════════════════════
#  ERROR TRACKING
# ═══════════════════════════════════════════════════════════

def log_error(module: str, error: str, severity: str = "error"):
    """Log an error from any module."""
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "module": module,
        "error": error[:200],
        "severity": severity,
    }
    _error_log.append(entry)

    # Keep max 100 errors
    if len(_error_log) > 100:
        _error_log.pop(0)


def log_command(command: str):
    """Track command usage stats."""
    _command_stats[command] += 1


def get_top_commands(n: int = 10) -> List[Tuple[str, int]]:
    """Get top N most used commands."""
    return sorted(_command_stats.items(), key=lambda x: x[1], reverse=True)[:n]


# ═══════════════════════════════════════════════════════════
#  FORMAT — BOSS DASHBOARD
# ═══════════════════════════════════════════════════════════

def format_spoc_dashboard(token: str = None) -> str:
    """Generate the FULL JARVIS SPOC Dashboard for Boss Deepak Kumar."""
    modules = check_module_health()
    apis = check_api_health(token)
    system = check_system_resources()
    threads = check_background_threads()

    now = datetime.now()
    lines = []

    # Header
    lines.append("🧠🔱 *J.A.R.V.I.S. SPOC DASHBOARD* 🔱🧠")
    lines.append("═" * 30)
    lines.append(f"👑 *Boss:* {BOSS_NAME}")
    lines.append(f"⏰ *Time:* {now.strftime('%H:%M IST, %d %b %Y')}")
    lines.append(f"⏱️ *Uptime:* {system.get('bot_uptime_str', 'N/A')}")
    lines.append("")

    # System Resources
    lines.append("💻 *SYSTEM RESOURCES*")
    lines.append("─" * 25)
    cpu = system.get("cpu_percent", -1)
    ram = system.get("ram_percent", -1)
    disk = system.get("disk_percent", -1)
    cpu_bar = _progress_bar(cpu)
    ram_bar = _progress_bar(ram)
    disk_bar = _progress_bar(disk)
    lines.append(f"🖥️ CPU: {cpu_bar} {cpu}%")
    lines.append(f"🧠 RAM: {ram_bar} {ram}% ({system.get('ram_used_gb', '?')}/{system.get('ram_total_gb', '?')} GB)")
    lines.append(f"💾 Disk: {disk_bar} {disk}%")
    lines.append(f"🐍 Python: {system.get('python_version', '?')}")
    lines.append(f"🧵 Threads: {system.get('threads_active', '?')}")
    lines.append("")

    # Background Threads Status
    lines.append("🔄 *BACKGROUND THREADS*")
    lines.append("─" * 25)
    for tid, tinfo in threads.items():
        icon = "🟢" if tinfo["alive"] else "🔴"
        lines.append(f"{icon} {tinfo['name']}")
    lines.append("")

    # API Health
    lines.append("🌐 *API HEALTH*")
    lines.append("─" * 25)
    for api_name, ainfo in apis.items():
        if ainfo["status"] == "healthy":
            icon = "🟢"
        elif ainfo["status"] in ("rate_limited", "degraded"):
            icon = "🟡"
        else:
            icon = "🔴"
        ms = ainfo.get("response_ms", 0)
        lines.append(f"{icon} {api_name}: {ainfo['status']} ({ms}ms)")
    lines.append("")

    # Module Status — grouped by type
    lines.append("📦 *MODULE STATUS (30+ Engines)*")
    lines.append("─" * 25)

    type_order = ["core", "stock", "crypto", "ml", "infra"]
    type_names = {"core": "🤖 Core", "stock": "📊 Stock Market", "crypto": "🪙 Crypto", "ml": "🧠 AI/ML", "infra": "⚙️ Infrastructure"}

    for mod_type in type_order:
        type_mods = {k: v for k, v in modules.items() if v.get("type") == mod_type}
        if not type_mods:
            continue
        lines.append(f"\n{type_names.get(mod_type, mod_type)}:")
        for mod_name, minfo in type_mods.items():
            if minfo["status"] == "alive":
                icon = "✅"
            elif minfo["status"] == "not_installed":
                icon = "⬜"
            else:
                icon = "❌"
            crit = "🔴" if minfo["critical"] else ""
            lines.append(f"  {icon} {minfo['icon']} {minfo['name']} {crit}")

    lines.append("")

    # Project stats
    total_mods = len(modules)
    alive = sum(1 for m in modules.values() if m["status"] == "alive")
    total_lines = sum(m.get("lines", 0) for m in modules.values())

    lines.append("📊 *PROJECT STATS*")
    lines.append("─" * 25)
    lines.append(f"📦 Modules: {alive}/{total_mods} alive")
    lines.append(f"📝 Total Lines: {total_lines:,}")
    lines.append(f"🐛 Errors (session): {len(_error_log)}")

    # Top commands
    top_cmds = get_top_commands(5)
    if top_cmds:
        lines.append("")
        lines.append("📈 *TOP COMMANDS*")
        lines.append("─" * 25)
        for cmd, count in top_cmds:
            lines.append(f"  /{cmd}: {count}x")

    # Recent errors
    if _error_log:
        lines.append("")
        lines.append(f"🐛 *RECENT ERRORS ({len(_error_log)})*")
        lines.append("─" * 25)
        for err in _error_log[-5:]:
            lines.append(f"  ⚠️ [{err['time']}] {err['module']}: {err['error'][:60]}")

    lines.append("")
    lines.append(f"🧠 JARVIS SPOC — reporting to {BOSS_NAME}")
    lines.append("🔱 _Main hoon na, Boss. Sab control mein hai._ 🔱")

    return "\n".join(lines)


def format_spoc_quick() -> str:
    """Quick one-line status for Boss."""
    modules = check_module_health()
    system = check_system_resources()
    threads = check_background_threads()

    alive = sum(1 for m in modules.values() if m["status"] == "alive")
    total = len(modules)
    thread_alive = sum(1 for t in threads.values() if t["alive"])
    thread_total = len(threads)
    cpu = system.get("cpu_percent", "?")
    ram = system.get("ram_percent", "?")
    uptime = system.get("bot_uptime_str", "?")

    return (
        f"🧠 *JARVIS SPOC Quick Report*\n"
        f"═══════════════════════════\n"
        f"👑 Boss: {BOSS_NAME}\n"
        f"📦 Modules: {alive}/{total} ✅\n"
        f"🔄 Threads: {thread_alive}/{thread_total} running\n"
        f"🖥️ CPU: {cpu}% | RAM: {ram}%\n"
        f"⏱️ Uptime: {uptime}\n"
        f"🐛 Errors: {len(_error_log)}\n"
        f"🔱 _Sab theek hai, {BOSS_NAME} sir!_"
    )


def format_spoc_voice() -> str:
    """Generate voice text for JARVIS SPOC report."""
    modules = check_module_health()
    system = check_system_resources()
    threads = check_background_threads()

    alive = sum(1 for m in modules.values() if m["status"] == "alive")
    total = len(modules)
    thread_alive = sum(1 for t in threads.values() if t["alive"])
    dead_threads = [t["name"] for t in threads.values() if not t["alive"]]
    errors = len(_error_log)
    uptime = system.get("bot_uptime_str", "unknown")

    voice = f"Namaste {BOSS_NAME} sir! Main JARVIS, aapki SPOC report de rahi hoon. "
    voice += f"Total {total} mein se {alive} modules active hain. "
    voice += f"{thread_alive} background threads chal rahe hain. "

    if dead_threads:
        voice += f"Warning: {', '.join(dead_threads)} band hai. "
    else:
        voice += "Saare threads perfectly chal rahe hain. "

    voice += f"Bot {uptime} se chal raha hai. "

    if errors > 0:
        voice += f"{errors} errors aayi hain is session mein. "
    else:
        voice += "Zero errors! Sab smooth chal raha hai. "

    voice += f"Main hoon na, boss. Sab control mein hai."
    return voice


def format_daily_briefing(token: str = None) -> str:
    """Generate JARVIS daily morning briefing for Boss."""
    modules = check_module_health()
    apis = check_api_health(token)
    system = check_system_resources()
    threads = check_background_threads()

    now = datetime.now()
    alive = sum(1 for m in modules.values() if m["status"] == "alive")
    total = len(modules)
    healthy_apis = sum(1 for a in apis.values() if a["status"] == "healthy")
    total_apis = len(apis)

    lines = []
    lines.append(f"🌅🧠 *JARVIS DAILY BRIEFING*")
    lines.append("═" * 30)
    lines.append(f"👑 *Good Morning, {BOSS_NAME} Sir!*")
    lines.append(f"📅 {now.strftime('%A, %d %B %Y')}")
    lines.append(f"⏰ {now.strftime('%H:%M IST')}")
    lines.append("")

    # Overall health
    health_pct = int((alive / total) * 100) if total > 0 else 0
    if health_pct >= 90:
        health_emoji = "🟢"
        health_text = "EXCELLENT"
    elif health_pct >= 70:
        health_emoji = "🟡"
        health_text = "GOOD"
    else:
        health_emoji = "🔴"
        health_text = "NEEDS ATTENTION"

    lines.append(f"{health_emoji} *Overall Health:* {health_text} ({health_pct}%)")
    lines.append(f"📦 Modules: {alive}/{total} active")
    lines.append(f"🌐 APIs: {healthy_apis}/{total_apis} healthy")
    lines.append(f"🔄 Threads: All running ✅" if all(t["alive"] for t in threads.values()) else f"🔄 Threads: Some stopped ⚠️")
    lines.append(f"⏱️ Uptime: {system.get('bot_uptime_str', 'N/A')}")
    lines.append("")

    # Issues
    dead_mods = [m for m, info in modules.items() if info["status"] == "error" and info.get("critical")]
    dead_threads = [t["name"] for t in threads.values() if not t["alive"]]
    dead_apis = [a for a, info in apis.items() if info["status"] in ("down", "timeout")]

    if dead_mods or dead_threads or dead_apis:
        lines.append("⚠️ *ISSUES DETECTED:*")
        for m in dead_mods:
            lines.append(f"  ❌ Module {m} DOWN")
        for t in dead_threads:
            lines.append(f"  ❌ Thread {t} stopped")
        for a in dead_apis:
            lines.append(f"  ❌ API {a} unreachable")
    else:
        lines.append("✅ *No issues detected — sab perfect!*")

    lines.append("")
    lines.append(f"🧠 _JARVIS ready for duty, {BOSS_NAME} sir!_")
    lines.append("💡 Type /spoc for full dashboard")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
#  BACKGROUND SPOC MONITOR THREAD
# ═══════════════════════════════════════════════════════════

def start_spoc(send_fn, voice_fn, token: str):
    """Start the JARVIS SPOC background monitoring thread."""
    global _spoc_running, _spoc_thread

    if _spoc_running:
        return

    _spoc_running = True

    def _spoc_loop():
        logger.info("[SPOC] 🧠 JARVIS SPOC STARTED — monitoring entire project for Boss Deepak Kumar")
        time.sleep(60)  # Wait for everything to boot

        while _spoc_running:
            try:
                # Health check every 5 minutes
                modules = check_module_health()
                apis = check_api_health(token)
                threads = check_background_threads()

                # Check for critical failures
                critical_dead = [
                    m for m, info in modules.items()
                    if info.get("critical") and info["status"] == "error"
                ]

                dead_threads = [
                    t["name"] for t in threads.values() if not t["alive"]
                ]

                # Smart critical alert — only alert if truly dead AND with cooldown
                # Ignore supervisor threads (they watch others)
                real_dead = [t for t in dead_threads if 'Supervisor' not in t]
                
                if critical_dead or real_dead:
                    # Cooldown: only alert once every 30 min for same set of issues
                    _alert_key = str(sorted(critical_dead + real_dead))
                    _now_ts = time.time()
                    _last_alert_ts = getattr(check_background_threads, '_last_alert_ts', 0)
                    _last_alert_key = getattr(check_background_threads, '_last_alert_key', '')
                    
                    if _alert_key != _last_alert_key or (_now_ts - _last_alert_ts) > 1800:
                        check_background_threads._last_alert_ts = _now_ts
                        check_background_threads._last_alert_key = _alert_key
                        
                        alert = f"🚨🧠 *JARVIS CRITICAL ALERT!*\n\n👑 {BOSS_NAME} sir, attention needed:\n\n"
                        for m in critical_dead:
                            alert += f"❌ Module *{m}* is DOWN!\n"
                        for t in real_dead:
                            alert += f"❌ Thread *{t}* stopped!\n"
                        alert += f"\n🛡️ _Auto-recovery attempting restart..._"
                        alert += f"\n💡 /spoc for full dashboard"

                        if BOSS_CHAT_ID:
                            try:
                                send_fn(BOSS_CHAT_ID, alert)
                            except:
                                pass
                    else:
                        logger.info(f"[SPOC] Skipping duplicate alert (cooldown active): {real_dead}")

                # Daily briefing at 8:30 AM
                global _daily_report_sent
                now = datetime.now()
                if now.hour == 8 and 25 <= now.minute <= 35 and not _daily_report_sent:
                    if BOSS_CHAT_ID:
                        try:
                            briefing = format_daily_briefing(token)
                            send_fn(BOSS_CHAT_ID, briefing)
                            if voice_fn:
                                voice_fn(BOSS_CHAT_ID,
                                    f"Good morning {BOSS_NAME} sir! Daily briefing ready hai. Saare systems check kar liye hain.",
                                    intent="greeting")
                            _daily_report_sent = True
                        except:
                            pass
                elif now.hour == 9:
                    _daily_report_sent = False

                global _last_health_check
                _last_health_check = now

            except Exception as e:
                logger.error(f"[SPOC] Health check error: {e}")

            # Sleep 5 minutes between checks
            for _ in range(300):
                if not _spoc_running:
                    break
                time.sleep(1)

    _spoc_thread = threading.Thread(target=_spoc_loop, daemon=True, name="jarvis-spoc")
    _spoc_thread.start()
    logger.info("[SPOC] 🧠 JARVIS SPOC background thread started")


def stop_spoc():
    """Stop SPOC monitoring."""
    global _spoc_running
    _spoc_running = False


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

def _format_uptime(seconds: float) -> str:
    """Format seconds into human-readable uptime."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    mins = int((seconds % 3600) // 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)


def _progress_bar(pct: float, length: int = 10) -> str:
    """Create a text progress bar."""
    if pct < 0:
        return "?" * length
    filled = int(pct / 100 * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
#  INDIAN SUPER ENGINE QUICK ACCESS
# ═══════════════════════════════════════════════════════════

def get_indian_super_engine():
    """Get the Indian Super Engine module if loaded."""
    try:
        import indian_stock_super_engine
        return indian_stock_super_engine
    except:
        return None

def quick_market_status() -> str:
    """Quick market status check."""
    eng = get_indian_super_engine()
    if eng:
        s = eng.get_market_status()
        return s.message
    return "Market status engine unavailable."

def quick_holidays(n=5) -> list:
    """Get upcoming NSE holidays."""
    eng = get_indian_super_engine()
    if eng:
        return eng.get_upcoming_holidays(n)
    return []

def quick_nifty_options(budget=2000.0):
    """Quick NIFTY options recommendation."""
    eng = get_indian_super_engine()
    if eng:
        return eng.recommend_best_options("NIFTY", budget, "auto")
    return None

def quick_sensex_options(budget=2000.0):
    """Quick SENSEX options recommendation."""
    eng = get_indian_super_engine()
    if eng:
        return eng.recommend_best_options("SENSEX", budget, "auto")
    return None

def quick_banknifty_options(budget=2000.0):
    """Quick BankNifty options recommendation."""
    eng = get_indian_super_engine()
    if eng:
        return eng.recommend_best_options("BANKNIFTY", budget, "auto")
    return None


__all__ = [
    "format_spoc_dashboard", "format_spoc_quick", "format_spoc_voice",
    "format_daily_briefing", "start_spoc", "stop_spoc",
    "check_module_health", "check_api_health", "check_system_resources",
    "check_background_threads", "log_error", "log_command",
    "BOSS_NAME", "BOSS_CHAT_ID",
    "quick_market_status", "quick_holidays",
    "quick_nifty_options", "quick_sensex_options", "quick_banknifty_options",
    "get_indian_super_engine",
]
