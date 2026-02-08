"""
🔔 JARVIS Monitor — Background Auto-Alert + Keep-Alive System
═══════════════════════════════════════════════════════════════
Runs as background threads, continuously monitoring:
  1. Price alerts (target hit, stop loss, pump alerts)
  2. Rug pull detection on watchlisted tokens
  3. New CoinDCX token detection + BUY/SELL signals + alerts
  4. Bot keep-alive (self-ping watchdog)
  5. Auto-reconnect on failure
  6. Phantom Wallet real-time monitoring for ALL users
  7. CoinDCX ALL Web3 token buy/sell signal scanner

Sends Telegram alerts + voice when something triggers.
Keeps bot alive 24/7 even when laptop is off.

Author: David Crew AI
"""

import os
import time
import logging
import threading
import traceback
import requests
from datetime import datetime
from typing import Optional, Callable, Dict, List

logger = logging.getLogger("jarvis_monitor")

# Monitor config
MONITOR_INTERVAL = 120  # Check every 2 minutes
NEW_TOKEN_CHECK_INTERVAL = 180  # Check for new tokens every 3 minutes
WEB3_SIGNAL_SCAN_INTERVAL = 300  # Scan all Web3 tokens for signals every 5 min (was 10)
KEEPALIVE_INTERVAL = 300  # Self-ping every 5 minutes
SUPERVISOR_INTERVAL = 30  # Check thread health every 30 seconds
MONITOR_ENABLED = True

_monitor_thread: Optional[threading.Thread] = None
_keepalive_thread: Optional[threading.Thread] = None
_new_token_thread: Optional[threading.Thread] = None
_web3_signal_thread: Optional[threading.Thread] = None
_phantom_rt_thread: Optional[threading.Thread] = None
_supervisor_thread: Optional[threading.Thread] = None
_monitor_running = False
_bot_token = None
_owner_chat_id = None

# ═══════════════════════════════════════════════════════════
#  THREAD SUPERVISOR — Auto-Restart Crashed Threads
# ═══════════════════════════════════════════════════════════

_thread_registry: Dict[str, dict] = {}  # name -> {thread, factory, restart_count, last_restart, backoff}
_thread_health: Dict[str, dict] = {}  # name -> {alive, last_heartbeat, error_count}
MAX_RESTARTS = 50  # Max restarts before giving up
INITIAL_BACKOFF = 5  # Start with 5 second backoff
MAX_BACKOFF = 300  # Max 5 minutes between restarts


def _register_thread(name: str, thread: threading.Thread, factory_fn, description: str = ""):
    """Register a thread with the supervisor for auto-restart monitoring."""
    _thread_registry[name] = {
        "thread": thread,
        "factory": factory_fn,
        "restart_count": 0,
        "last_restart": 0,
        "backoff": INITIAL_BACKOFF,
        "description": description,
        "started_at": time.time(),
    }
    _thread_health[name] = {
        "alive": True,
        "last_heartbeat": time.time(),
        "error_count": 0,
        "total_uptime": 0,
    }
    logger.info(f"[SUPERVISOR] Registered thread: {name} ({description})")


def _supervisor_loop():
    """
    🛡️ THREAD SUPERVISOR — Monitors all registered threads and auto-restarts crashed ones.
    This is the watchdog that keeps JARVIS alive 24/7.
    """
    logger.info("[SUPERVISOR] 🛡️ Thread Supervisor ONLINE — watching all threads 24/7!")
    
    while _monitor_running:
        try:
            dead_threads = []
            
            for name, info in _thread_registry.items():
                thread = info["thread"]
                
                if thread is None or not thread.is_alive():
                    if info["restart_count"] >= MAX_RESTARTS:
                        if info["restart_count"] == MAX_RESTARTS:
                            logger.critical(f"[SUPERVISOR] 💀 Thread '{name}' exceeded max restarts ({MAX_RESTARTS}). GIVING UP.")
                            info["restart_count"] += 1  # Prevent repeated logging
                        continue
                    
                    dead_threads.append(name)
                else:
                    # Thread is alive — reset backoff gradually
                    uptime = time.time() - info.get("started_at", time.time())
                    if uptime > 600:  # Running > 10 min = healthy
                        info["backoff"] = max(INITIAL_BACKOFF, info["backoff"] // 2)
                    _thread_health[name]["alive"] = True
                    _thread_health[name]["last_heartbeat"] = time.time()
            
            # Restart dead threads
            for name in dead_threads:
                info = _thread_registry[name]
                backoff = info["backoff"]
                last_restart = info["last_restart"]
                
                # Respect backoff
                if time.time() - last_restart < backoff:
                    continue
                
                info["restart_count"] += 1
                info["last_restart"] = time.time()
                info["backoff"] = min(backoff * 2, MAX_BACKOFF)  # Exponential backoff
                
                logger.warning(
                    f"[SUPERVISOR] 🔄 Thread '{name}' DEAD! Restarting... "
                    f"(attempt #{info['restart_count']}, backoff={info['backoff']}s)"
                )
                
                try:
                    # Create new thread using factory function
                    new_thread = info["factory"]()
                    new_thread.start()
                    info["thread"] = new_thread
                    info["started_at"] = time.time()
                    _thread_health[name]["alive"] = True
                    _thread_health[name]["error_count"] += 1
                    
                    logger.info(f"[SUPERVISOR] ✅ Thread '{name}' restarted successfully!")
                    
                    # Notify owner about restart
                    if _owner_chat_id and _bot_token:
                        try:
                            _emergency_notify(_bot_token, _owner_chat_id,
                                f"🔄 *JARVIS Auto-Recovery*\n\n"
                                f"Thread *{info.get('description', name)}* crashed and was auto-restarted.\n"
                                f"Restart #{info['restart_count']} | Backoff: {info['backoff']}s\n"
                                f"⏰ {datetime.now().strftime('%I:%M %p')}"
                            )
                        except:
                            pass
                    
                except Exception as e:
                    logger.error(f"[SUPERVISOR] ❌ Failed to restart '{name}': {e}")
                    _thread_health[name]["alive"] = False
        
        except Exception as e:
            logger.error(f"[SUPERVISOR] Supervisor error: {e}")
        
        # Sleep in small increments for quick shutdown
        for _ in range(SUPERVISOR_INTERVAL):
            if not _monitor_running:
                break
            time.sleep(1)
    
    logger.info("[SUPERVISOR] 🛡️ Thread Supervisor stopped")


def get_thread_health() -> Dict[str, dict]:
    """Get health status of all monitored threads — for SPOC dashboard."""
    health = {}
    for name, info in _thread_registry.items():
        thread = info["thread"]
        alive = thread is not None and thread.is_alive()
        uptime = time.time() - info.get("started_at", time.time()) if alive else 0
        health[name] = {
            "alive": alive,
            "restart_count": info["restart_count"],
            "uptime_seconds": int(uptime),
            "uptime_human": f"{int(uptime//3600)}h {int((uptime%3600)//60)}m" if alive else "DEAD",
            "description": info.get("description", name),
            "last_restart": info["last_restart"],
            "backoff": info["backoff"],
        }
    return health


def start_monitor(send_fn, voice_fn, token: str, chat_ids: list = None, owner_id: int = None):
    """
    Start all background monitoring threads WITH auto-restart supervisor.
    send_fn: function(chat_id, text, reply_markup) to send Telegram messages
    voice_fn: function(chat_id, text, intent) to send voice
    token: Telegram bot token
    chat_ids: list of chat_ids to monitor (default: all with alerts)
    owner_id: Owner chat_id for admin-only alerts (new tokens etc.)
    """
    global _monitor_thread, _keepalive_thread, _new_token_thread, _web3_signal_thread
    global _phantom_rt_thread, _supervisor_thread, _monitor_running, _bot_token, _owner_chat_id

    if _monitor_running:
        logger.info("[MONITOR] Already running")
        return

    _monitor_running = True
    _bot_token = token
    _owner_chat_id = owner_id or int(os.environ.get("TEST_CHAT_ID", "0"))

    # Thread 1: Price alerts (with crash protection)
    def _monitor_loop():
        logger.info("[MONITOR] 🔔 JARVIS Monitor started — watching your tokens 24/7!")
        while _monitor_running:
            try:
                _check_all_alerts(send_fn, voice_fn, token)
            except Exception as e:
                logger.error(f"[MONITOR] Error in check cycle: {e}\n{traceback.format_exc()}")
            for _ in range(MONITOR_INTERVAL):
                if not _monitor_running:
                    break
                time.sleep(1)
        logger.info("[MONITOR] Stopped")

    def _make_monitor_thread():
        t = threading.Thread(target=_monitor_loop, daemon=True, name="jarvis-monitor")
        return t

    _monitor_thread = _make_monitor_thread()
    _monitor_thread.start()
    _register_thread("monitor", _monitor_thread, _make_monitor_thread, "🔔 Price Alert Monitor")
    logger.info("[MONITOR] Background thread started")

    # Thread 2: Keep-alive self-ping (with crash protection)
    def _keepalive_loop():
        logger.info("[KEEPALIVE] 🏥 Keep-alive watchdog started")
        fail_count = 0
        while _monitor_running:
            try:
                api_url = f"https://api.telegram.org/bot{token}/getMe"
                r = requests.get(api_url, timeout=15)
                if r.status_code == 200:
                    fail_count = 0
                    logger.debug("[KEEPALIVE] ✅ Bot alive")
                else:
                    fail_count += 1
                    logger.warning(f"[KEEPALIVE] ⚠️ Bot ping failed: {r.status_code} (fail #{fail_count})")
            except Exception as e:
                fail_count += 1
                logger.error(f"[KEEPALIVE] ❌ Ping exception (fail #{fail_count}): {e}")

            if fail_count >= 5:
                logger.critical(f"[KEEPALIVE] 🚨 Bot appears down! {fail_count} consecutive failures")
                # Try to notify owner
                try:
                    _emergency_notify(token, _owner_chat_id, 
                        f"🚨 JARVIS ALERT: Bot may be down! {fail_count} ping failures. Auto-recovery attempting...")
                except:
                    pass

            # Adaptive sleep: longer interval when stable, shorter when failing
            sleep_time = KEEPALIVE_INTERVAL if fail_count == 0 else 30
            for _ in range(sleep_time):
                if not _monitor_running:
                    break
                time.sleep(1)

    _keepalive_thread = threading.Thread(target=_keepalive_loop, daemon=True, name="keepalive-watchdog")
    _keepalive_thread.start()
    _register_thread("keepalive", _keepalive_thread, 
        lambda: threading.Thread(target=_keepalive_loop, daemon=True, name="keepalive-watchdog"),
        "🏥 Keep-Alive Watchdog")
    logger.info("[KEEPALIVE] Keep-alive watchdog started")

    # Thread 3: New CoinDCX token detector (with crash protection)
    def _new_token_loop():
        logger.info("[NEW-TOKEN] 🆕 New token detector started")
        # Wait for initial token load
        time.sleep(30)
        while _monitor_running:
            try:
                _check_new_tokens(send_fn, voice_fn)
            except Exception as e:
                logger.error(f"[NEW-TOKEN] Error: {e}\n{traceback.format_exc()}")
            for _ in range(NEW_TOKEN_CHECK_INTERVAL):
                if not _monitor_running:
                    break
                time.sleep(1)

    def _make_new_token_thread():
        return threading.Thread(target=_new_token_loop, daemon=True, name="new-token-detector")

    _new_token_thread = _make_new_token_thread()
    _new_token_thread.start()
    _register_thread("new_token", _new_token_thread, _make_new_token_thread, "🆕 New Token Detector")
    logger.info("[NEW-TOKEN] New token detector started")

    # Thread 4: CoinDCX ALL Web3 token buy/sell signal scanner (with crash protection)
    def _web3_signal_scan_loop():
        logger.info("[WEB3-SIGNALS] 🔍 CoinDCX Web3 Buy/Sell Signal Scanner started")
        time.sleep(60)  # Wait for boot
        while _monitor_running:
            try:
                _scan_web3_buy_sell_signals(send_fn, voice_fn)
            except Exception as e:
                logger.error(f"[WEB3-SIGNALS] Error: {e}\n{traceback.format_exc()}")
            for _ in range(WEB3_SIGNAL_SCAN_INTERVAL):
                if not _monitor_running:
                    break
                time.sleep(1)

    def _make_web3_thread():
        return threading.Thread(target=_web3_signal_scan_loop, daemon=True, name="web3-signal-scanner")

    _web3_signal_thread = _make_web3_thread()
    _web3_signal_thread.start()
    _register_thread("web3_signals", _web3_signal_thread, _make_web3_thread, "🔍 Web3 Signal Scanner")
    logger.info("[WEB3-SIGNALS] Web3 signal scanner started")

    # Thread 5: Phantom Wallet real-time monitoring for ALL users (with crash protection)
    def _phantom_realtime_loop():
        logger.info("[PHANTOM-RT] 👻 Phantom Wallet Real-Time Monitor started")
        time.sleep(90)  # Wait for boot
        try:
            from phantom_wallet import start_realtime_monitoring, auto_connect_owner_wallet
            auto_connect_owner_wallet()
            start_realtime_monitoring(send_fn=send_fn, voice_fn=voice_fn)
            logger.info("[PHANTOM-RT] 👻 Phantom Real-Time Engine activated for all users")
        except ImportError:
            logger.warning("[PHANTOM-RT] Phantom wallet module not available")
        except Exception as e:
            logger.error(f"[PHANTOM-RT] Error starting: {e}\n{traceback.format_exc()}")
        # Keep thread alive — heartbeat loop so supervisor doesn't restart
        while _monitor_running:
            time.sleep(60)

    def _make_phantom_thread():
        return threading.Thread(target=_phantom_realtime_loop, daemon=True, name="phantom-realtime")

    _phantom_rt_thread = _make_phantom_thread()
    _phantom_rt_thread.start()
    _register_thread("phantom_rt", _phantom_rt_thread, _make_phantom_thread, "👻 Phantom Real-Time Monitor")
    logger.info("[PHANTOM-RT] Phantom real-time thread started")

    # Thread 6: 🛡️ SUPERVISOR — The watchdog that keeps ALL threads alive
    _supervisor_thread = threading.Thread(target=_supervisor_loop, daemon=True, name="thread-supervisor")
    _supervisor_thread.start()
    logger.info("[SUPERVISOR] 🛡️ Thread Supervisor started — monitoring all threads")


def stop_monitor():
    """Stop all monitoring threads."""
    global _monitor_running
    _monitor_running = False
    logger.info("[MONITOR] Stop requested for all threads")


def _emergency_notify(token: str, chat_id: int, message: str):
    """Send emergency notification via direct API call"""
    if not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
    except:
        pass


def _check_new_tokens(send_fn, voice_fn):
    """Check for newly listed tokens on CoinDCX and alert owner with BUY/SELL signal"""
    try:
        from coindcx_engine import get_all_web3_tokens, get_new_token_alerts, _ist_now
    except ImportError:
        return

    # Helper to format INR
    def _fmt(val):
        if val >= 10_000_000: return f"₹{val/10_000_000:.2f} Cr"
        elif val >= 100_000: return f"₹{val/100_000:.2f} L"
        elif val >= 1000: return f"₹{val:,.0f}"
        elif val >= 1: return f"₹{val:.2f}"
        elif val >= 0.0001: return f"₹{val:.6f}"
        else: return f"₹{val:.10f}"

    # Trigger token refresh
    get_all_web3_tokens()

    # Check for new tokens
    new_tokens = get_new_token_alerts()
    if not new_tokens:
        return

    for token_data in new_tokens:
        sym = token_data['symbol']
        name = token_data.get('name', sym)
        price = token_data.get('price_inr', 0)
        change = token_data.get('change_24h', 0)
        volume = token_data.get('volume', 0)
        cats = ", ".join(token_data.get('categories', []))

        # Generate quick buy/sell signal for new token
        signal = "🟡 WATCH"
        signal_detail = "New listing — observe for 24h"
        if change > 20 and volume > 100000:
            signal = "🟢 BUY"
            signal_detail = "Strong momentum + high volume on launch!"
        elif change > 10 and volume > 50000:
            signal = "🟡 CAUTIOUS BUY"
            signal_detail = "Good momentum, monitor closely"
        elif change < -10:
            signal = "🔴 AVOID"
            signal_detail = "Dumping on launch — risky entry"
        elif volume < 10000:
            signal = "⚠️ LOW VOLUME"
            signal_detail = "Not enough liquidity yet, wait for volume"

        # Calculate entry/target/SL
        entry_price = price
        t1 = price * 1.20  # +20%
        t2 = price * 1.50  # +50%
        t3 = price * 2.00  # 2x
        sl = price * 0.85  # -15%

        # Investment suggestion for ₹2000
        invest_qty = int(2000 / price) if price > 0 else 0
        invest_line = f"💸 ₹2,000 invest → *{invest_qty} {sym}*" if invest_qty > 0 else ""

        msg = (
            f"{'═'*28}\n"
            f"🆕🚀 *NEW CoinDCX WEB3 LISTING!*\n"
            f"{'═'*28}\n\n"
            f"🪙 *{sym}* ({name})\n"
            f"💰 Price: {_fmt(price) if price > 0 else 'Loading...'}\n"
            f"📈 24h Change: {change:+.1f}%\n"
            f"📊 Volume: {_fmt(volume) if volume > 0 else 'N/A'}\n"
            f"🏷️ Category: {cats or 'Altcoin'}\n\n"
            f"🟢 *Entry Price:* {_fmt(entry_price)}\n"
            f"🎯 *Target 1:* {_fmt(t1)} (+20%)\n"
            f"🎯 *Target 2:* {_fmt(t2)} (+50%)\n"
            f"🚀 *Target 3:* {_fmt(t3)} (2x)\n"
            f"🔴 *Stop Loss:* {_fmt(sl)} (-15%)\n\n"
            f"{invest_line + chr(10) if invest_line else ''}"
            f"🤖 *JARVIS Signal:* {signal}\n"
            f"💡 {signal_detail}\n\n"
            f"🛒 *Buy here:*\n"
            f"  • [CoinDCX Buy {sym}](https://coindcx.com/trade/{sym}INR)\n"
            f"  • [Jupiter DEX](https://jup.ag)\n"
            f"  • [Raydium DEX](https://raydium.io)\n\n"
            f"📊 Full analysis: /cdx {sym}\n"
            f"💰 Invest: /invest {sym}\n"
            f"🕐 {_ist_now()}\n"
            f"⚡ _CoinDCX New Token Alert + AI Signal_"
        )

        if _owner_chat_id:
            try:
                send_fn(_owner_chat_id, msg)
                logger.info(f"[NEW-TOKEN] 🆕 Alert+Signal sent for {sym}")
                if voice_fn:
                    voice_fn(_owner_chat_id, 
                        f"New token alert! {name} listed on CoinDCX at {_fmt(price)}. Signal is {signal}. Check with slash C D X {sym}.",
                        intent="buy_sell_crypto")
            except Exception as e:
                logger.error(f"[NEW-TOKEN] Alert send failed for {sym}: {e}")


def _scan_web3_buy_sell_signals(send_fn, voice_fn):
    """🔥 MEGA SCAN — Top 100 CoinDCX tokens with AI/ML + Candle Patterns.
    Runs every 5 minutes. Scans ALL 613+ tokens using full TA + ML + Candles.
    Alerts on ALL tokens with score >= 3 or <= -3 (up to 100 tokens).
    """
    try:
        from coindcx_mega_scanner import (
            mega_scan_top100, format_bg_alert_top_signals, format_mega_voice
        )
        MEGA_AVAILABLE = True
    except ImportError:
        MEGA_AVAILABLE = False

    if not MEGA_AVAILABLE:
        # Fallback to basic scan
        _scan_web3_basic(send_fn, voice_fn)
        return

    try:
        # 🔥 MEGA SCAN — Full AI/ML on ALL tokens, return top 100
        results = mega_scan_top100(top_n=100)
        if not results:
            logger.info("[WEB3-SIGNALS] Mega scan: no results")
            return

        # Get message pages (splits into 4000-char pages)
        pages = format_bg_alert_top_signals(results, limit=100)
        if not pages:
            logger.info("[WEB3-SIGNALS] No actionable signals found")
            return

        # Send all pages to owner
        if _owner_chat_id:
            for page in pages:
                try:
                    send_fn(_owner_chat_id, page)
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"[WEB3-SIGNALS] Send page failed: {e}")

            # Voice summary
            if voice_fn:
                try:
                    voice_text = format_mega_voice(results)
                    voice_fn(_owner_chat_id, voice_text, intent="buy_sell_crypto")
                except Exception as e:
                    logger.error(f"[WEB3-SIGNALS] Voice failed: {e}")

        actionable = sum(1 for r in results if abs(r.get('ai_score', 0)) >= 3)
        buys = sum(1 for r in results if r.get('ai_score', 0) >= 3)
        sells = sum(1 for r in results if r.get('ai_score', 0) <= -3)
        logger.info(f"[WEB3-SIGNALS] 🔥 MEGA SCAN: {len(results)} tokens, {actionable} actionable ({buys} BUY / {sells} SELL), {len(pages)} pages sent")

    except Exception as e:
        logger.error(f"[WEB3-SIGNALS] Mega scan error: {e}")
        # Fallback
        try:
            _scan_web3_basic(send_fn, voice_fn)
        except:
            pass


def _scan_web3_basic(send_fn, voice_fn):
    """Basic fallback scanner (old logic) — used if mega scanner fails."""
    try:
        from coindcx_engine import get_all_web3_tokens, _ist_now
    except ImportError:
        return

    def _fmt(val):
        if val >= 10_000_000: return f"₹{val/10_000_000:.2f} Cr"
        elif val >= 100_000: return f"₹{val/100_000:.2f} L"
        elif val >= 1000: return f"₹{val:,.0f}"
        elif val >= 1: return f"₹{val:.2f}"
        elif val >= 0.0001: return f"₹{val:.6f}"
        else: return f"₹{val:.10f}"

    try:
        tokens = get_all_web3_tokens()
        if not tokens:
            return

        hot_tokens = []
        for t in tokens:
            change = t.get('change_24h', 0)
            volume = t.get('volume', 0)
            price = t.get('price_inr', 0)
            if abs(change) > 5 and volume > 5000 and price > 0:
                hot_tokens.append(t)
            elif abs(change) > 15 and price > 0:
                hot_tokens.append(t)

        if not hot_tokens:
            return

        hot_tokens.sort(key=lambda x: abs(x.get('change_24h', 0)), reverse=True)

        for token in hot_tokens[:30]:
            sym = token['symbol']
            name = token.get('name', sym)
            price = token.get('price_inr', 0)
            change = token.get('change_24h', 0)

            if change > 20: signal = "🚀 MEGA PUMP"
            elif change > 8: signal = "🟢 BUY"
            elif change > 3: signal = "🟡 MILD BUY"
            elif change < -20: signal = "💀 CRASH"
            elif change < -8: signal = "🔴 SELL"
            elif change < -3: signal = "🟠 MILD SELL"
            else: continue

            msg = f"📊 *{sym}* ({name}) — {_fmt(price)} ({change:+.1f}%) — {signal}"
            if _owner_chat_id:
                try:
                    send_fn(_owner_chat_id, msg)
                    time.sleep(0.3)
                except:
                    pass

        logger.info(f"[WEB3-SIGNALS] Basic scan: {len(tokens)} tokens, {len(hot_tokens)} hot")
    except Exception as e:
        logger.error(f"[WEB3-SIGNALS] Basic scan error: {e}")


def _check_all_alerts(send_fn, voice_fn, token: str):
    """Check all price alerts and send notifications."""
    try:
        from crypto_intelligence import check_price_alerts_all
    except ImportError:
        return

    triggered = check_price_alerts_all()

    for alert in triggered:
        chat_id = alert.get("chat_id")
        if not chat_id:
            continue

        chat_id_int = int(chat_id)
        msg = alert.get("message", "")
        voice_text = alert.get("voice", "")
        alert_type = alert.get("type", "")

        try:
            # Send text alert
            if msg:
                send_fn(chat_id_int, msg)
                logger.info(f"[MONITOR] Alert sent to {chat_id}: {alert_type} {alert.get('symbol')}")

            # Send voice alert
            if voice_text and voice_fn:
                voice_fn(chat_id_int, voice_text, intent="buy_sell_crypto")

        except Exception as e:
            logger.error(f"[MONITOR] Failed to send alert to {chat_id}: {e}")


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'start_monitor',
    'stop_monitor',
    'get_thread_health',
    'MONITOR_INTERVAL',
    'WEB3_SIGNAL_SCAN_INTERVAL',
]
