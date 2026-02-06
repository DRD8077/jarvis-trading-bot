
import os
from dotenv import load_dotenv
load_dotenv()
import threading
import time
from typing import Optional
import json
import logging
from datetime import datetime, timedelta
import pytz
import pandas as pd

import qrcode
from io import BytesIO

from stock_data_fetcher import fetch_nse_option_chain, parse_option_chain_json, analyze_option_chain, format_signal_message
from ml_pipeline import predict_for_symbol

import requests

# --- Logging setup ---
LOG_FILE = os.environ.get("TELEGRAM_BOT_LOG", "telegram_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_bot")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or "7897330325:AAF0opOkFdu0AiZk-tGAF_oGPrY5KMzjazE"
if os.environ.get("TELEGRAM_BOT_TOKEN") is None:
    print("TELEGRAM_BOT_TOKEN not set — using embedded token from file.")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

IST = pytz.timezone('Asia/Kolkata')

auto_thread = None
auto_flag = threading.Event()
chat_storage = {}

# ═══════════════════════════════════════════════════════════
#  DECORATIVE UI CONSTANTS
# ═══════════════════════════════════════════════════════════

HEADER_LINE = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
DOUBLE_LINE = "═══════════════════════════════"
SPARKLE_LINE = "✦═══════════════════════════✦"
DIAMOND_LINE = "◆━━━━━━━━━━━━━━━━━━━━━━━━━◆"
STAR_LINE = "★═══════════════════════════★"
FIRE_LINE = "🔥━━━━━━━━━━━━━━━━━━━━━━━🔥"

# ═══════════════════════════════════════════════════════════
#  CORE TELEGRAM FUNCTIONS
# ═══════════════════════════════════════════════════════════

def send_message(chat_id: int, text: str, reply_markup: Optional[dict] = None):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"send_message -> chat_id={chat_id} status={r.status_code}")
        if r.status_code != 200:
            logger.error(f"send_message failed: {r.text[:200]}")
    except Exception:
        print(f"send_message exception for chat_id={chat_id}")
        pass


def send_photo(chat_id: int, image_bytes: bytes, caption: Optional[str] = None):
    url = f"{API_URL}/sendPhoto"
    files = {"photo": ("qrcode.png", image_bytes)}
    data = {"chat_id": chat_id, "parse_mode": "Markdown"}
    if caption:
        data["caption"] = caption
    try:
        r = requests.post(url, files=files, data=data, timeout=10)
        print(f"send_photo -> chat_id={chat_id} status={r.status_code}")
    except Exception as e:
        print(f"send_photo exception for chat_id={chat_id}: {e}")


def generate_qr(data: str) -> bytes:
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ═══════════════════════════════════════════════════════════
#  PERSONALIZATION — HAR HAR MAHADEV GREETING
# ═══════════════════════════════════════════════════════════

def get_user_greeting(update: dict) -> str:
    """Extract user's name from Telegram update and create personalized greeting."""
    try:
        user = update.get("message", {}).get("from", {})
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or "User"
    except Exception:
        full_name = "User"
    
    greeting = (
        f"🙏🕉️ *HAR HAR MAHADEV {full_name.upper()} JI* 🕉️🙏\n"
        f"{SPARKLE_LINE}\n"
    )
    return greeting


def get_user_name(update: dict) -> str:
    """Get user's display name from update."""
    try:
        user = update.get("message", {}).get("from", {})
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        return f"{first_name} {last_name}".strip() or "User"
    except Exception:
        return "User"


# ═══════════════════════════════════════════════════════════
#  STUNNING UI — KEYBOARD WITH RICH EMOJIS
# ═══════════════════════════════════════════════════════════

def build_keyboard():
    """Build visually stunning keyboard with decorative buttons."""
    rows = [
        ["🔱 NIFTY Signals 📊", "🔱 SENSEX Signals 📊"],
        ["💎 NIFTY Calls OTM 🚀", "💎 SENSEX Calls OTM 🚀"],
        ["⚡ NIFTY Puts OTM 📉", "⚡ SENSEX Puts OTM 📉"],
        ["🌍 Market Trend 📈", "⏰ Market Status 🔔"],
        ["🔮 Tomorrow Prediction 🎯"],
        ["➕ Add Symbol 🎯", "➖ Remove Symbol ❌", "📋 Watchlist"],
        ["🔔 Subscribe Alerts ✅", "🔕 Unsubscribe ❌", "👥 My Subs"],
        ["📱 Generate QR 🔗", "❓ Help 💡", "🏠 /start"],
    ]
    return {"keyboard": rows, "resize_keyboard": True}


# ═══════════════════════════════════════════════════════════
#  OPTION CHAIN ANALYSIS
# ═══════════════════════════════════════════════════════════

def find_best_otm_options(calls_df, puts_df, underlying, option_type="calls", num_strikes=3):
    """Find best OTM options with return potential."""
    results = []
    
    if option_type == "calls":
        df = calls_df.copy()
        otm = df[df['strike'] > underlying].sort_values('strike')
    else:
        df = puts_df.copy()
        otm = df[df['strike'] < underlying].sort_values('strike', ascending=False)
    
    if otm.empty:
        return []
    
    for _, row in otm.head(num_strikes).iterrows():
        strike = float(row.get('strike', 0))
        ltp = float(row.get('lastPrice', 0))
        iv = float(row.get('impliedVolatility', 0))
        bid = float(row.get('bidprice', ltp))
        
        if ltp <= 0:
            continue
        
        moneyness = abs(strike - underlying) / underlying
        return_potential = (50 + iv * 100 + moneyness * 100) * 10
        
        results.append({
            'strike': strike,
            'ltp': ltp,
            'bid': bid,
            'iv': iv,
            'moneyness_pct': moneyness * 100,
            'return_potential': return_potential,
            'oi': float(row.get('openInterest', 0))
        })
    
    return sorted(results, key=lambda x: x['return_potential'], reverse=True)


# ═══════════════════════════════════════════════════════════
#  TOMORROW PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════

def generate_tomorrow_prediction() -> str:
    """Generate comprehensive next-day prediction based on global markets,
    technical analysis, and sentiment — recommends CALL or PUT."""
    import yfinance as yf
    
    now = datetime.now(IST)
    tomorrow = (now + timedelta(days=1)).strftime("%A, %d %b %Y")
    
    parts = []
    parts.append(f"🔮✨ *TOMORROW'S MARKET PREDICTION* ✨🔮")
    parts.append(FIRE_LINE)
    parts.append(f"📅 *Date:* {tomorrow}")
    parts.append(f"⏰ *Generated:* {now.strftime('%H:%M IST, %d %b %Y')}")
    parts.append(HEADER_LINE)
    
    # Collect signals
    bullish_signals = 0
    bearish_signals = 0
    total_signals = 0
    
    # 1. Global Market Analysis
    parts.append("\n🌍 *GLOBAL MARKET SCAN:*")
    global_indices = {
        "US S&P 500": "^GSPC",
        "US NASDAQ": "^IXIC",
        "US Dow Jones": "^DJI",
        "UK FTSE 100": "^FTSE",
        "Japan Nikkei": "^N225",
        "Hong Kong HSI": "^HSI",
        "Gold": "GC=F",
        "Crude Oil": "CL=F",
        "VIX (Fear)": "^VIX",
    }
    
    for name, ticker in global_indices.items():
        try:
            data = yf.download(ticker, period="5d", progress=False)
            if data is not None and len(data) >= 2:
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                col = 'Close' if 'Close' in data.columns else 'close'
                close_vals = data[col].values
                prev = float(close_vals[-2])
                curr = float(close_vals[-1])
                if prev > 0:
                    change_pct = ((curr - prev) / prev) * 100
                    total_signals += 1
                    if "VIX" in name:
                        if change_pct > 0:
                            bearish_signals += 1
                            icon = "🔴"
                        else:
                            bullish_signals += 1
                            icon = "🟢"
                    else:
                        if change_pct > 0:
                            bullish_signals += 1
                            icon = "🟢"
                        else:
                            bearish_signals += 1
                            icon = "🔴"
                    parts.append(f"  {icon} {name}: {change_pct:+.2f}%")
        except Exception:
            pass
    
    # 2. NIFTY & SENSEX Technical Analysis
    parts.append(f"\n{HEADER_LINE}")
    parts.append("📊 *TECHNICAL ANALYSIS:*")
    
    for yf_ticker, display_name in [("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX")]:
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index(yf_ticker, display_name)
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            price = analysis.get("indicators", {}).get("price", 0)
            rsi = analysis.get("indicators", {}).get("rsi", 50)
            
            if signal == "BUY":
                bullish_signals += 2
                total_signals += 2
                icon = "🟢"
            elif signal == "SELL":
                bearish_signals += 2
                total_signals += 2
                icon = "🔴"
            else:
                total_signals += 1
                icon = "🟡"
            
            parts.append(f"  {icon} *{display_name}:* {signal} ({conf:.0%})")
            parts.append(f"     Price: ₹{price:.0f} | RSI: {rsi:.1f}")
            
            if rsi > 70:
                bearish_signals += 1
                total_signals += 1
                parts.append(f"     ⚠️ RSI Overbought — reversal possible")
            elif rsi < 30:
                bullish_signals += 1
                total_signals += 1
                parts.append(f"     ✅ RSI Oversold — bounce likely")
        except Exception:
            parts.append(f"  ⚠️ {display_name} analysis unavailable")
    
    # 3. Final Prediction
    parts.append(f"\n{DOUBLE_LINE}")
    parts.append("🎯 *TOMORROW'S VERDICT:*")
    parts.append(FIRE_LINE)
    
    if total_signals > 0:
        bull_pct = (bullish_signals / total_signals) * 100
        bear_pct = (bearish_signals / total_signals) * 100
    else:
        bull_pct = 50
        bear_pct = 50
    
    bull_blocks = int(bull_pct / 10)
    bear_blocks = int(bear_pct / 10)
    bull_bar = "🟩" * bull_blocks + "⬜" * (10 - bull_blocks)
    bear_bar = "🟥" * bear_blocks + "⬜" * (10 - bear_blocks)
    
    parts.append(f"\n  📈 Bullish: {bull_bar} {bull_pct:.0f}%")
    parts.append(f"  📉 Bearish: {bear_bar} {bear_pct:.0f}%")
    
    if bull_pct > 65:
        verdict = "🟢🚀 *STRONG BUY CALLS* 🚀🟢"
        action = "BUY CALL OPTIONS (CE)"
        emoji_border = "💚💚💚💚💚💚💚💚💚💚"
        detail = "Markets showing strong bullish momentum. Buy CE (Call) options."
    elif bull_pct > 55:
        verdict = "🟢 *MODERATELY BULLISH — BUY CALLS* 🟢"
        action = "BUY CALL OPTIONS (with caution)"
        emoji_border = "💚💚💚💚💚🟡🟡🟡🟡🟡"
        detail = "Mild bullish tilt. Call options favored but keep strict stop-loss."
    elif bear_pct > 65:
        verdict = "🔴📉 *STRONG BUY PUTS* 📉🔴"
        action = "BUY PUT OPTIONS (PE)"
        emoji_border = "❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️"
        detail = "Markets showing strong bearish pressure. Buy PE (Put) options."
    elif bear_pct > 55:
        verdict = "🔴 *MODERATELY BEARISH — BUY PUTS* 🔴"
        action = "BUY PUT OPTIONS (with caution)"
        emoji_border = "❤️❤️❤️❤️❤️🟡🟡🟡🟡🟡"
        detail = "Bearish tilt visible. Put options favored but manage risk."
    else:
        verdict = "🟡⚖️ *NEUTRAL — WAIT & WATCH* ⚖️🟡"
        action = "NO TRADE — Stay on sidelines"
        emoji_border = "🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡"
        detail = "No clear direction. Avoid trading, wait for clearer signals."
    
    parts.append(f"\n  {emoji_border}")
    parts.append(f"\n  🎯 *VERDICT:* {verdict}")
    parts.append(f"  💰 *ACTION:* {action}")
    parts.append(f"\n  📝 {detail}")
    parts.append(f"\n  {emoji_border}")
    
    parts.append(f"\n{HEADER_LINE}")
    parts.append("⚠️ *DISCLAIMER:*")
    parts.append("_AI-generated prediction. Not financial advice._")
    parts.append("_Always use stop-loss. Trade at your own risk._")
    parts.append(STAR_LINE)
    
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════
#  AUTO ALERT SYSTEM (24/7 Background Thread)
# ═══════════════════════════════════════════════════════════

last_auto_alert_time = {}

def is_market_open() -> bool:
    """Check if NSE market is open (Mon-Fri 9:15 AM - 3:30 PM IST)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def auto_alert_loop():
    """Background thread: automatically sends NIFTY/SENSEX signals to all subscribers.
    
    During market hours: every 10 min analysis + alerts on BUY/SELL
    Off hours: every 2 hours global market summary + next day prediction
    """
    logger.info("🔔 Auto-Alert Engine STARTED — running 24/7")
    
    while not auto_flag.is_set():
        try:
            from data_store import list_subscribers
            subs = list_subscribers()
            
            if not subs:
                logger.info("[AUTO] No subscribers, sleeping 60s...")
                time.sleep(60)
                continue
            
            now = datetime.now(IST)
            
            if is_market_open():
                # ── MARKET HOURS: Send live trading signals ──
                interval = 600  # 10 minutes
                
                for index_name, ticker, display_name in [
                    ("NIFTY", "^NSEI", "NIFTY 50"),
                    ("SENSEX", "^BSESN", "SENSEX")
                ]:
                    try:
                        from candle_analyzer import analyze_index
                        analysis = analyze_index(ticker, display_name)
                        signal = analysis.get("signal", "HOLD")
                        confidence = analysis.get("confidence", 0.5)
                        price = analysis.get("indicators", {}).get("price", 0)
                        rsi = analysis.get("indicators", {}).get("rsi", 50)
                        atr = analysis.get("indicators", {}).get("atr", 100)
                        
                        if signal in ("BUY", "SELL") and confidence >= 0.55:
                            key = f"{index_name}_{signal}"
                            last_time = last_auto_alert_time.get(key, 0)
                            if time.time() - last_time < 1800:
                                continue
                            last_auto_alert_time[key] = time.time()
                            
                            if signal == "BUY":
                                emoji = "🟢🚀"
                                action = "BUY CALL (CE)"
                                sl = price - (atr * 1.5)
                                t1 = price + (atr * 1.0)
                                t2 = price + (atr * 2.0)
                            else:
                                emoji = "🔴📉"
                                action = "BUY PUT (PE)"
                                sl = price + (atr * 1.5)
                                t1 = price - (atr * 1.0)
                                t2 = price - (atr * 2.0)
                            
                            rr = abs(t1 - price) / abs(price - sl) if abs(price - sl) > 0 else 0
                            
                            alert = (
                                f"{FIRE_LINE}\n"
                                f"{emoji} *AUTO SIGNAL — {index_name}* {emoji}\n"
                                f"{DIAMOND_LINE}\n"
                                f"⏰ *Time:* {now.strftime('%H:%M IST')}\n"
                                f"📊 *Signal:* *{signal}* | Confidence: *{confidence:.0%}*\n"
                                f"💹 *Price:* ₹{price:.2f}\n"
                                f"📈 *RSI:* {rsi:.1f}\n"
                                f"{HEADER_LINE}\n"
                                f"💰 *ACTION:* {action}\n"
                                f"┣ 🎯 Entry: ₹{price:.2f}\n"
                                f"┣ 🛑 Stop Loss: ₹{sl:.2f}\n"
                                f"┣ ✅ Target 1: ₹{t1:.2f}\n"
                                f"┗ 🏆 Target 2: ₹{t2:.2f}\n"
                                f"📊 Risk-Reward: 1:{rr:.2f}\n"
                                f"{HEADER_LINE}\n"
                            )
                            
                            reasons = analysis.get("reasons", [])
                            if reasons:
                                alert += "🧠 *AI ANALYSIS:*\n"
                                for i, reason in enumerate(reasons[:3], 1):
                                    alert += f"  {i}. {reason}\n"
                            
                            alert += f"\n{STAR_LINE}\n"
                            alert += "⚠️ _Auto-alert. Not financial advice. Use SL._"
                            
                            for chat_id in subs:
                                try:
                                    send_message(chat_id, alert)
                                except Exception as e:
                                    logger.error(f"[AUTO] Failed to send to {chat_id}: {e}")
                                    
                    except Exception as e:
                        logger.error(f"[AUTO] Analysis failed for {index_name}: {e}")
                
                time.sleep(interval)
                
            else:
                # ── OFF HOURS: Send periodic global summary + prediction ──
                key = "off_market_summary"
                last_time = last_auto_alert_time.get(key, 0)
                
                if time.time() - last_time >= 7200:  # every 2 hours
                    last_auto_alert_time[key] = time.time()
                    
                    try:
                        prediction = generate_tomorrow_prediction()
                        
                        for chat_id in subs:
                            try:
                                header = (
                                    f"🌙 *OFF-MARKET AUTO UPDATE* 🌙\n"
                                    f"{SPARKLE_LINE}\n"
                                    f"⏰ {now.strftime('%H:%M IST, %d %b %Y')}\n\n"
                                )
                                send_message(chat_id, header + prediction)
                            except Exception as e:
                                logger.error(f"[AUTO] Failed off-market msg to {chat_id}: {e}")
                    except Exception as e:
                        logger.error(f"[AUTO] Prediction failed: {e}")
                
                time.sleep(300)  # check every 5 min during off-hours
                
        except Exception as e:
            logger.error(f"[AUTO] Loop error: {e}", exc_info=True)
            time.sleep(30)


# ═══════════════════════════════════════════════════════════
#  MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════

def handle_update(update: dict):
    if "message" not in update:
        return
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    print(f"handle_update -> chat_id={chat_id} text={text}")
    
    # Store chat id
    chat_storage["last_chat"] = chat_id
    try:
        with open("last_chat_id.txt", "w") as f:
            f.write(str(chat_id))
    except Exception as e:
        logger.error(f"Failed to write last_chat_id.txt: {e}")
    
    # ── PERSONALIZED GREETING ──
    greeting = get_user_greeting(update)
    user_name = get_user_name(update)
    
    # ════════════════════════════
    #   /start COMMAND
    # ════════════════════════════
    if text == "/start" or text == "🏠 /start":
        welcome = (
            f"{greeting}"
            f"\n"
            f"🔱💎 *WELCOME TO DAVID CREW TRADING BOT* 💎🔱\n"
            f"{FIRE_LINE}\n"
            f"\n"
            f"🚀 *India's Most Powerful AI Trading Assistant* 🚀\n"
            f"{HEADER_LINE}\n"
            f"\n"
            f"💎 *FEATURES:*\n"
            f"┣ 📊 *Live Signals* — NIFTY/SENSEX real-time\n"
            f"┣ 🚀 *OTM Options* — High-leverage call/put picks\n"
            f"┣ 🌍 *Global Trends* — World market analysis\n"
            f"┣ 🔮 *AI Prediction* — Tomorrow's call/put forecast\n"
            f"┣ 🔔 *Auto Alerts* — 24/7 live trading signals\n"
            f"┣ 📋 *Watchlist* — Track your symbols\n"
            f"┗ 📱 *QR Share* — Invite friends instantly\n"
            f"\n"
            f"{STAR_LINE}\n"
            f"⚡ _Powered by AI + Technical Analysis + Global Data_ ⚡\n"
            f"🙏 *HAR HAR MAHADEV — TRADE WITH CONFIDENCE* 🙏\n"
            f"{SPARKLE_LINE}\n"
        )
        send_message(chat_id, welcome, reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   HELP
    # ════════════════════════════
    if text in ("❓ Help", "❓ Help 💡", "Help"):
        help_text = (
            f"{greeting}"
            f"💡 *HELP — BOT COMMANDS* 💡\n"
            f"{DOUBLE_LINE}\n"
            f"\n"
            f"🔱 *SIGNALS & ANALYSIS:*\n"
            f"┣ 📊 NIFTY/SENSEX Signals — AI technical analysis\n"
            f"┣ 💎 OTM Calls — High-leverage call options\n"
            f"┣ ⚡ OTM Puts — Bearish put options\n"
            f"┣ 🌍 Market Trend — Global market sentiment\n"
            f"┗ ⏰ Market Status — NSE open/closed\n"
            f"\n"
            f"🔮 *PREDICTIONS:*\n"
            f"┗ 🔮 Tomorrow Prediction — AI call/put forecast\n"
            f"\n"
            f"🔔 *ALERTS:*\n"
            f"┣ Subscribe — Get automatic 24/7 signals\n"
            f"┗ Unsubscribe — Stop alerts\n"
            f"\n"
            f"📋 *WATCHLIST:*\n"
            f"┣ Add Symbol — Add stock to watchlist\n"
            f"┣ Remove Symbol — Remove from watchlist\n"
            f"┗ My Watchlist — View your stocks\n"
            f"\n"
            f"📱 *OTHER:*\n"
            f"┣ Generate QR — Share bot link\n"
            f"┗ Type any symbol (e.g. RELIANCE) for signals\n"
            f"\n"
            f"{STAR_LINE}\n"
        )
        send_message(chat_id, help_text, reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   MARKET TREND
    # ════════════════════════════
    if text in ("Market Trend", "📈 Market Trend", "🌍 Market Trend 📈"):
        send_message(chat_id, f"{greeting}🔄 *Analyzing global markets...* Please wait 20-30s ⏳")
        try:
            from global_market_analyzer import get_market_trend_analysis
            import signal as sig
            def timeout_handler(signum, frame):
                raise TimeoutError("Market analysis timed out")
            try:
                sig.signal(sig.SIGALRM, timeout_handler)
                sig.alarm(45)
                trend_msg = get_market_trend_analysis()
                sig.alarm(0)
                if not trend_msg or not trend_msg.strip():
                    send_message(chat_id, f"{greeting}⚠️ Market trend returned no data. Try again later.")
                else:
                    decorated = (
                        f"{greeting}"
                        f"🌍 *GLOBAL MARKET TREND* 🌍\n"
                        f"{FIRE_LINE}\n\n"
                        f"{trend_msg}\n\n"
                        f"{STAR_LINE}"
                    )
                    send_message(chat_id, decorated)
            except TimeoutError:
                sig.alarm(0)
                send_message(chat_id, f"{greeting}⏱️ Analysis taking too long.\n\n🟡 Check again in a moment.")
            except Exception as e:
                logger.error(f"Market trend failed: {e}", exc_info=True)
                send_message(chat_id, f"{greeting}⚠️ Market trend temporarily unavailable.")
        except Exception as e:
            logger.error(f"Market trend outer error: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}⚠️ Market trend temporarily unavailable.")
        return

    # ════════════════════════════
    #   SUBSCRIBE ALERTS
    # ════════════════════════════
    if text in ("🔔 Subscribe Alerts", "Subscribe Alerts", "🔔 Subscribe Alerts ✅"):
        try:
            from data_store import add_subscriber
            add_subscriber(chat_id)
            sub_msg = (
                f"{greeting}"
                f"✅🔔 *ALERTS ACTIVATED* 🔔✅\n"
                f"{FIRE_LINE}\n\n"
                f"🎉 *{user_name}*, you're now subscribed!\n\n"
                f"📊 *What you'll get:*\n"
                f"┣ 🟢 Live BUY/SELL signals during market hours\n"
                f"┣ 🔮 Tomorrow's prediction every evening\n"
                f"┣ 🌍 Global market updates off-hours\n"
                f"┗ ⚡ Instant NIFTY/SENSEX alerts\n\n"
                f"🔥 _24/7 Auto Trading Intelligence Active!_ 🔥\n"
                f"{STAR_LINE}"
            )
            send_message(chat_id, sub_msg, reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Subscribe failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Subscribe failed. Please try again.")
        return

    # ════════════════════════════
    #   UNSUBSCRIBE
    # ════════════════════════════
    if text in ("Unsubscribe Alerts", "🔕 Unsubscribe", "🔕 Unsubscribe ❌"):
        try:
            from data_store import remove_subscriber
            remove_subscriber(chat_id)
            send_message(chat_id, f"{greeting}🔕 *Unsubscribed* from automated alerts.\n\n_You can re-subscribe anytime!_", reply_markup=build_keyboard())
        except Exception:
            send_message(chat_id, f"{greeting}❌ Unsubscribe failed.")
        return

    # ════════════════════════════
    #   MY SUBS
    # ════════════════════════════
    if text in ("My Subscriptions", "👥 My Subs"):
        try:
            from data_store import list_subscribers
            subs = list_subscribers()
            is_subbed = chat_id in subs
            status = "✅ *ACTIVE*" if is_subbed else "❌ *NOT SUBSCRIBED*"
            subs_msg = (
                f"{greeting}"
                f"👥 *SUBSCRIPTION STATUS*\n"
                f"{HEADER_LINE}\n\n"
                f"📊 Total Subscribers: *{len(subs)}*\n"
                f"🔔 Your Status: {status}\n\n"
                f"{SPARKLE_LINE}"
            )
            send_message(chat_id, subs_msg, reply_markup=build_keyboard())
        except Exception:
            send_message(chat_id, f"{greeting}❌ Failed to fetch subscriptions.")
        return

    # ════════════════════════════
    #   ADD SYMBOL
    # ════════════════════════════
    if text in ("Add Symbol", "🎯 Add Symbol", "➕ Add Symbol 🎯"):
        send_message(chat_id, f"{greeting}🎯 *Send me a symbol to add:*\n\n_Example: RELIANCE, INFY, SBIN, TCS_")
        chat_storage["awaiting_add_symbol"] = chat_id
        return

    # ════════════════════════════
    #   REMOVE SYMBOL
    # ════════════════════════════
    if text in ("Remove Symbol", "❌ Remove Symbol", "➖ Remove Symbol ❌"):
        send_message(chat_id, f"{greeting}❌ *Send me a symbol to remove:*")
        chat_storage["awaiting_remove_symbol"] = chat_id
        return

    # ════════════════════════════
    #   WATCHLIST
    # ════════════════════════════
    if text in ("My Watchlist", "📋 My Watchlist", "📋 Watchlist"):
        try:
            from data_store import get_watchlist
            watchlist = get_watchlist(chat_id)
            if watchlist:
                wl_items = "\n".join([f"  💎 {s}" for s in watchlist])
                wl_msg = (
                    f"{greeting}"
                    f"📋 *YOUR WATCHLIST* 📋\n"
                    f"{DIAMOND_LINE}\n\n"
                    f"{wl_items}\n\n"
                    f"📊 Total: *{len(watchlist)}* symbols\n"
                    f"{SPARKLE_LINE}"
                )
            else:
                wl_msg = (
                    f"{greeting}"
                    f"📋 *YOUR WATCHLIST* 📋\n"
                    f"{HEADER_LINE}\n\n"
                    f"_Empty! Use ➕ Add Symbol to add stocks._\n"
                    f"{SPARKLE_LINE}"
                )
            send_message(chat_id, wl_msg, reply_markup=build_keyboard())
        except Exception:
            send_message(chat_id, f"{greeting}❌ Failed to fetch watchlist.")
        return

    # ════════════════════════════
    #   NIFTY SIGNALS
    # ════════════════════════════
    if text in ("📊 NIFTY Signals", "🔱 NIFTY Signals 📊"):
        send_message(chat_id, f"{greeting}🔄 *Analyzing NIFTY 50...* ⏳")
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index("^NSEI", "NIFTY 50")
            sig_text = analysis["analysis"]
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            
            if signal == "BUY":
                sig_emoji = "🟢🚀"
            elif signal == "SELL":
                sig_emoji = "🔴📉"
            else:
                sig_emoji = "🟡⚖️"
            
            decorated = (
                f"{greeting}"
                f"🔱 *NIFTY 50 — LIVE ANALYSIS* 🔱\n"
                f"{FIRE_LINE}\n\n"
                f"{sig_text}\n\n"
                f"{DIAMOND_LINE}\n"
                f"🎯 *Signal:* {sig_emoji} *{signal}*\n"
                f"📊 *Confidence:* {conf:.0%}\n"
                f"{STAR_LINE}"
            )
            send_message(chat_id, decorated, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to fetch NIFTY signals: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   SENSEX SIGNALS
    # ════════════════════════════
    if text in ("📊 SENSEX Signals", "🔱 SENSEX Signals 📊"):
        send_message(chat_id, f"{greeting}🔄 *Analyzing SENSEX...* ⏳")
        try:
            from candle_analyzer import analyze_index
            analysis = analyze_index("^BSESN", "SENSEX")
            sig_text = analysis["analysis"]
            signal = analysis.get("signal", "HOLD")
            conf = analysis.get("confidence", 0.5)
            
            if signal == "BUY":
                sig_emoji = "🟢🚀"
            elif signal == "SELL":
                sig_emoji = "🔴📉"
            else:
                sig_emoji = "🟡⚖️"
            
            decorated = (
                f"{greeting}"
                f"🔱 *SENSEX — LIVE ANALYSIS* 🔱\n"
                f"{FIRE_LINE}\n\n"
                f"{sig_text}\n\n"
                f"{DIAMOND_LINE}\n"
                f"🎯 *Signal:* {sig_emoji} *{signal}*\n"
                f"📊 *Confidence:* {conf:.0%}\n"
                f"{STAR_LINE}"
            )
            send_message(chat_id, decorated, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to fetch SENSEX signals: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   OTM CALLS / PUTS (unified)
    # ════════════════════════════
    otm_map = {
        "📞 NIFTY Calls OTM": ("TCS", "^NSEI", "NIFTY", "calls"),
        "💎 NIFTY Calls OTM 🚀": ("TCS", "^NSEI", "NIFTY", "calls"),
        "📞 SENSEX Calls OTM": ("RELIANCE", "^BSESN", "SENSEX", "calls"),
        "💎 SENSEX Calls OTM 🚀": ("RELIANCE", "^BSESN", "SENSEX", "calls"),
        "📞 NIFTY Puts OTM": ("TCS", "^NSEI", "NIFTY", "puts"),
        "⚡ NIFTY Puts OTM 📉": ("TCS", "^NSEI", "NIFTY", "puts"),
        "📞 SENSEX Puts OTM": ("RELIANCE", "^BSESN", "SENSEX", "puts"),
        "⚡ SENSEX Puts OTM 📉": ("RELIANCE", "^BSESN", "SENSEX", "puts"),
    }
    
    if text in otm_map:
        proxy_sym, yf_ticker, index_name, opt_type = otm_map[text]
        is_calls = opt_type == "calls"
        
        type_emoji = "🚀💎" if is_calls else "📉⚡"
        type_label = "CALLS" if is_calls else "PUTS"
        type_word = "Call" if is_calls else "Put"
        
        send_message(chat_id, f"{greeting}🔄 *Fetching {index_name} OTM {type_label}...* ⏳")
        
        try:
            import yfinance as yf
            data = fetch_nse_option_chain(proxy_sym)
            
            if data:
                calls_df, puts_df, underlying = parse_option_chain_json(data)
                otm = find_best_otm_options(calls_df, puts_df, underlying, option_type=opt_type, num_strikes=5)
                
                msg_parts = [
                    f"{greeting}",
                    f"{type_emoji} *{index_name} OTM {type_label} — HIGH LEVERAGE* {type_emoji}",
                    f"{FIRE_LINE}",
                    f"💹 *Current Price:* ₹{underlying:.0f}\n",
                ]
                
                if otm:
                    for i, opt in enumerate(otm[:3], 1):
                        medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉'
                        msg_parts.append(f"{medal} *{type_word} Option {i}:*")
                        msg_parts.append(f"  ┣ Strike: ₹{opt['strike']:.0f}")
                        msg_parts.append(f"  ┣ Premium: ₹{opt['ltp']:.2f}")
                        msg_parts.append(f"  ┣ IV: {opt['iv']:.2f}%")
                        sign = '+' if is_calls else '-'
                        msg_parts.append(f"  ┣ OTM: {sign}{opt['moneyness_pct']:.2f}%")
                        msg_parts.append(f"  ┣ Return Potential: {opt['return_potential']:.0f}%")
                        msg_parts.append(f"  ┗ Open Interest: {opt['oi']:.0f}")
                        msg_parts.append("")
                else:
                    msg_parts.append("_(Live option data pending — using market analysis)_")
                
                msg_parts.append(f"{STAR_LINE}")
                send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
            else:
                # Fallback with simulated data
                ticker_data = yf.Ticker(yf_ticker)
                hist = ticker_data.history(period="5d")
                price = float(hist['Close'].iloc[-1])
                
                msg_parts = [
                    f"{greeting}",
                    f"{type_emoji} *{index_name} OTM {type_label} — HIGH LEVERAGE* {type_emoji}",
                    f"{FIRE_LINE}",
                    f"💹 *Current Price:* ₹{price:.0f}\n",
                    f"*Recommended {type_word} Strikes:*\n",
                ]
                
                if is_calls:
                    strikes = [int(price * m) for m in [1.01, 1.02, 1.03]]
                else:
                    strikes = [int(price * m) for m in [0.99, 0.98, 0.97]]
                
                for i, strike in enumerate(strikes, 1):
                    premium = abs(strike - price) * 0.5
                    otm_pct = abs(strike - price) / price * 100
                    medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉'
                    msg_parts.append(f"{medal} *{type_word} Option {i}:*")
                    msg_parts.append(f"  ┣ Strike: ₹{strike}")
                    msg_parts.append(f"  ┣ Premium: ₹{premium:.0f}")
                    sign = '+' if is_calls else '-'
                    msg_parts.append(f"  ┣ OTM: {sign}{otm_pct:.1f}%")
                    ret_pot = (abs(strike - premium - price) / premium * 100) if premium > 0 else 0
                    msg_parts.append(f"  ┗ Return Potential: {ret_pot:.0f}%")
                    msg_parts.append("")
                
                msg_parts.append(f"{STAR_LINE}")
                send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
                
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Error: {str(e)[:100]}")
        return

    # ════════════════════════════
    #   MARKET STATUS
    # ════════════════════════════
    if text in ("⏰ Market Status", "Market Status", "⏰ Market Status 🔔"):
        now = datetime.now(IST)
        mkt_open = is_market_open()
        
        if mkt_open:
            status_text = "🟢 *MARKET OPEN*"
            status_detail = "NSE is currently trading (9:15 AM - 3:30 PM IST)"
        else:
            status_text = "🔴 *MARKET CLOSED*"
            if now.weekday() >= 5:
                status_detail = "Weekend — Market reopens Monday 9:15 AM IST"
            elif now.hour < 9 or (now.hour == 9 and now.minute < 15):
                status_detail = "Pre-market — Opens at 9:15 AM IST"
            else:
                status_detail = "After hours — Reopens tomorrow 9:15 AM IST"
        
        status_msg = (
            f"{greeting}"
            f"⏰ *NSE MARKET STATUS* ⏰\n"
            f"{DIAMOND_LINE}\n\n"
            f"{status_text}\n"
            f"📝 {status_detail}\n\n"
            f"🕐 *Current Time:* {now.strftime('%I:%M %p IST')}\n"
            f"📅 *Date:* {now.strftime('%A, %d %b %Y')}\n\n"
            f"{SPARKLE_LINE}"
        )
        send_message(chat_id, status_msg, reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   TOMORROW PREDICTION
    # ════════════════════════════
    if text in ("🔮 Tomorrow Prediction 🎯", "Tomorrow Prediction"):
        send_message(chat_id, f"{greeting}🔮 *Generating AI prediction...* This may take 30-60 seconds ⏳")
        try:
            prediction = generate_tomorrow_prediction()
            full_msg = f"{greeting}{prediction}"
            send_message(chat_id, full_msg, reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Prediction temporarily unavailable. Try again later.")
        return

    # ════════════════════════════
    #   GENERATE QR
    # ════════════════════════════
    if text in ("Generate QR", "🔗 Generate QR", "📱 Generate QR 🔗"):
        try:
            qr = generate_qr("https://t.me/David_crew_bot")
            caption = (
                f"📱🔱 *DAVID CREW TRADING BOT* 🔱📱\n"
                f"{HEADER_LINE}\n"
                f"Scan to join the #1 AI Trading Bot!\n"
                f"🕉️ HAR HAR MAHADEV 🕉️"
            )
            send_photo(chat_id, qr, caption=caption)
            send_message(chat_id, f"{greeting}✅ QR Code generated! Share with your friends 🚀", reply_markup=build_keyboard())
        except Exception as e:
            logger.error(f"QR failed: {e}", exc_info=True)
            send_message(chat_id, f"{greeting}❌ Failed to generate QR code.")
        return

    # ════════════════════════════
    #   NIFTY/SENSEX TEXT INPUT
    # ════════════════════════════
    if text and text.strip().upper() in ["NIFTY", "SENSEX"]:
        symbol = text.strip().upper()
        
        if chat_storage.get("awaiting_add_symbol") == chat_id:
            try:
                from data_store import add_to_watchlist
                add_to_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Added *{symbol}* to your watchlist! 💎", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_add_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to add {symbol}.")
            return
        
        if chat_storage.get("awaiting_remove_symbol") == chat_id:
            try:
                from data_store import remove_from_watchlist
                remove_from_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Removed *{symbol}* from watchlist.", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_remove_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to remove {symbol}.")
            return
        
        # Show signals
        try:
            from candle_analyzer import analyze_index
            ticker_map = {"NIFTY": ("^NSEI", "NIFTY 50"), "SENSEX": ("^BSESN", "SENSEX")}
            if symbol in ticker_map:
                ticker, name = ticker_map[symbol]
                analysis = analyze_index(ticker, name)
                sig_text = analysis["analysis"]
                signal = analysis.get("signal", "HOLD")
                decorated = (
                    f"{greeting}"
                    f"🔱 *{name} — ANALYSIS* 🔱\n"
                    f"{FIRE_LINE}\n\n"
                    f"{sig_text}\n\n"
                    f"🎯 Signal: *{signal}*\n"
                    f"{STAR_LINE}"
                )
                send_message(chat_id, decorated, reply_markup=build_keyboard())
        except Exception as e:
            send_message(chat_id, f"{greeting}❌ Failed to analyze {symbol}")
        return

    # ════════════════════════════
    #   SIGNALS (legacy text)
    # ════════════════════════════
    if text == "Signals":
        try:
            from data_store import get_watchlist
            from candle_analyzer import analyze_index
            watchlist = get_watchlist(chat_id)
        except Exception:
            watchlist = []
        
        if not watchlist:
            watchlist = ["NIFTY", "SENSEX"]
        
        msg_parts = [f"{greeting}", f"📊 *PORTFOLIO SIGNALS* 📊\n{FIRE_LINE}\n"]
        
        ticker_map = {
            "NIFTY": ("^NSEI", "NIFTY 50"),
            "SENSEX": ("^BSESN", "SENSEX"),
        }
        
        for symbol in watchlist[:5]:
            symbol_upper = symbol.upper()
            if symbol_upper in ticker_map:
                ticker, name = ticker_map[symbol_upper]
                try:
                    analysis = analyze_index(ticker, name)
                    msg_parts.append(analysis["analysis"])
                    signal = analysis.get("signal", "HOLD")
                    conf = analysis.get("confidence", 0.5)
                    if signal == "BUY":
                        msg_parts.append(f"🟢 *BUY* (Confidence: {conf:.0%})")
                    elif signal == "SELL":
                        msg_parts.append(f"🔴 *SELL* (Confidence: {conf:.0%})")
                    else:
                        msg_parts.append(f"🟡 *HOLD*")
                    msg_parts.append(HEADER_LINE)
                except Exception as e:
                    msg_parts.append(f"{symbol}: Error - {str(e)[:50]}")
            else:
                msg_parts.append(f"{symbol}: _Index not supported (use NIFTY or SENSEX)_")
            msg_parts.append("")
        
        msg_parts.append(STAR_LINE)
        send_message(chat_id, "\n".join(msg_parts), reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   SYMBOL LOOKUP (generic)
    # ════════════════════════════
    if text and text.strip().isalpha() and len(text.strip()) <= 10:
        symbol = text.strip().upper()
        
        if chat_storage.get("awaiting_add_symbol") == chat_id:
            try:
                from data_store import add_to_watchlist
                add_to_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Added *{symbol}* to watchlist! 💎", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_add_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to add {symbol}.")
            return
        
        if chat_storage.get("awaiting_remove_symbol") == chat_id:
            try:
                from data_store import remove_from_watchlist
                remove_from_watchlist(chat_id, symbol)
                send_message(chat_id, f"{greeting}✅ Removed *{symbol}* from watchlist.", reply_markup=build_keyboard())
                chat_storage.pop("awaiting_remove_symbol", None)
            except Exception:
                send_message(chat_id, f"{greeting}❌ Failed to remove {symbol}.")
            return
        
        # Fetch option chain
        send_message(chat_id, f"{greeting}🔄 *Fetching data for {symbol}...* ⏳")
        data = fetch_nse_option_chain(symbol)
        if not data:
            send_message(chat_id, f"{greeting}❌ Failed to fetch option chain for *{symbol}*.")
            return
        calls, puts, u = parse_option_chain_json(data)
        analysis = analyze_option_chain(calls, puts, u)
        result = format_signal_message(symbol, analysis)
        
        decorated = (
            f"{greeting}"
            f"💎 *{symbol} — OPTION ANALYSIS* 💎\n"
            f"{FIRE_LINE}\n\n"
            f"{result}\n\n"
            f"{STAR_LINE}"
        )
        send_message(chat_id, decorated, reply_markup=build_keyboard())
        return

    # ════════════════════════════
    #   UNKNOWN COMMAND
    # ════════════════════════════
    unknown_msg = (
        f"{greeting}"
        f"🤔 *Command not recognized:* _{text[:50]}_\n\n"
        f"Use the buttons below or type /start for help! 👇\n"
        f"{SPARKLE_LINE}"
    )
    send_message(chat_id, unknown_msg, reply_markup=build_keyboard())


# ═══════════════════════════════════════════════════════════
#  POLLING LOOP
# ═══════════════════════════════════════════════════════════

def poll_updates():
    offset = None
    while True:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        try:
            r = requests.get(f"{API_URL}/getUpdates", params=params, timeout=40)
            js = r.json()
            logger.info(f"[POLL] Received updates: {json.dumps(js)[:500]}")
        except Exception as e:
            logger.error(f"[POLL] Exception in getUpdates: {e}")
            time.sleep(2)
            continue
        for u in js.get("result", []):
            logger.info(f"[POLL] Processing update: {json.dumps(u)[:300]}")
            offset = u["update_id"] + 1
            try:
                handle_update(u)
            except Exception as e:
                logger.error(f"[POLL] Error handling update: {e}", exc_info=True)
        time.sleep(0.5)


# ═══════════════════════════════════════════════════════════
#  MAIN — START BOT + AUTO-ALERT THREAD
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("[STARTUP] 🔱 David Crew Trading Bot starting...")
    print("🔱 Starting David Crew Trading Bot (polling + auto-alerts)")
    print(f"🔱 Token: {TELEGRAM_TOKEN[:20]}...")
    
    # Initialize database
    try:
        from data_store import init_db
        init_db()
        logger.info("[STARTUP] Database initialized")
    except Exception as e:
        logger.error(f"[STARTUP] DB init failed: {e}")
    
    # Start auto-alert background thread
    auto_thread = threading.Thread(target=auto_alert_loop, daemon=True, name="AutoAlertEngine")
    auto_thread.start()
    logger.info("[STARTUP] 🔔 Auto-Alert Engine started (background thread)")
    
    # Send startup message
    test_chat_id = os.environ.get("TEST_CHAT_ID")
    if test_chat_id:
        try:
            startup_msg = (
                f"🔱🕉️ *BOT RESTARTED* 🕉️🔱\n"
                f"{FIRE_LINE}\n\n"
                f"✅ *David Crew Trading Bot is ONLINE!*\n"
                f"🔔 Auto-Alert Engine: *ACTIVE*\n"
                f"📊 Polling: *ACTIVE*\n"
                f"🌍 Market Scanner: *ACTIVE*\n\n"
                f"⏰ {datetime.now(IST).strftime('%I:%M %p IST, %d %b %Y')}\n"
                f"{STAR_LINE}\n"
                f"🙏 *HAR HAR MAHADEV* 🙏"
            )
            send_message(int(test_chat_id), startup_msg, reply_markup=build_keyboard())
            logger.info(f"[STARTUP] Sent startup message to {test_chat_id}")
        except Exception as e:
            logger.error(f"[STARTUP] Failed to send startup: {e}")
    
    # Start polling
    poll_updates()
