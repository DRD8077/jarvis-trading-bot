"""
Automated real-time alerter for NIFTY/SENSEX.
Runs only during IST market hours (9:30 AM - 3:30 PM IST).
Generates BUY/SELL alerts with entry/exit levels and position sizing.
"""

import os
import time
import logging
from datetime import datetime
import pytz
import requests
from candle_analyzer import analyze_index, fetch_index_candles
from data_store import list_subscribers, get_alert_threshold

IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MIN = 30
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MIN = 30

WATCHLIST = os.environ.get("WATCHLIST", "NIFTY,SENSEX").split(",")
INTERVAL = int(os.environ.get("ALERTER_INTERVAL", "120"))

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

TICKER_MAP = {
    "NIFTY": ("^NSEI", "NIFTY 50"),
    "SENSEX": ("^BSESN", "SENSEX"),
}

# Track last alert time to avoid spamming
last_alert_time = {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def is_market_open() -> bool:
    """Check if NSE market is open."""
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0)
    return market_open <= now <= market_close


def send_message(chat_id: int, text: str):
    """Send Telegram message."""
    try:
        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        logging.exception("Failed to send message to %s: %s", chat_id, e)


def calculate_position_size(symbol: str) -> dict:
    """Calculate position size based on symbol."""
    if "NIFTY" in symbol:
        return {"qty": 1, "lot_size": 25}  # 1 lot = 25 units
    else:  # SENSEX
        return {"qty": 1, "lot_size": 1}   # 1 lot = 1 unit


def generate_trading_alert(symbol: str, analysis: dict, chat_id: int) -> bool:
    """Generate and send detailed trading alert."""
    
    signal = analysis.get("signal", "HOLD")
    confidence = analysis.get("confidence", 0)
    price = analysis["indicators"].get("price", 0)
    
    # Only send BUY/SELL alerts, not HOLD
    if signal == "HOLD":
        return False
    
    # Avoid duplicate alerts within 5 minutes
    key = f"{symbol}_{signal}"
    last_time = last_alert_time.get(key, 0)
    if time.time() - last_time < 300:  # 5 min cooldown
        return False
    
    last_alert_time[key] = time.time()
    
    # Calculate sizing and entry/exit levels
    pos_info = calculate_position_size(symbol)
    
    # Entry level = current price
    entry = price
    
    # Stop loss and target based on ATR
    atr = analysis["indicators"].get("atr", 100)
    rsi = analysis["indicators"].get("rsi", 50)
    
    if signal == "BUY":
        stop_loss = entry - (atr * 1.5)
        target1 = entry + (atr * 1.0)
        target2 = entry + (atr * 2.0)
        emoji = "🟢"
    else:  # SELL
        stop_loss = entry + (atr * 1.5)
        target1 = entry - (atr * 1.0)
        target2 = entry - (atr * 2.0)
        emoji = "🔴"
    
    # Build alert message
    alert_msg = (
        f"{emoji} *{signal} SIGNAL - {symbol}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ *Time:* {datetime.now(IST).strftime('%H:%M IST')}\n"
        f"📊 *Confidence:* {confidence:.0%}\n"
        f"📈 *RSI:* {rsi:.1f}\n\n"
        f"💰 *PRICE LEVELS:*\n"
        f"├ Entry: ₹{entry:.2f}\n"
        f"├ Stop Loss: ₹{stop_loss:.2f}\n"
        f"├ Target 1: ₹{target1:.2f}\n"
        f"└ Target 2: ₹{target2:.2f}\n\n"
        f"📦 *POSITION:*\n"
        f"├ Quantity: {pos_info['qty']} lot\n"
        f"└ Units: {pos_info['qty'] * pos_info['lot_size']} units\n\n"
        f"🧠 *AI ANALYSIS:*\n"
    )
    
    # Add key reasons (limit to 3)
    for i, reason in enumerate(analysis.get("reasons", [])[:3], 1):
        alert_msg += f"{i}. {reason}\n"
    
    # Calculate and display risk-reward
    if entry != stop_loss:
        rr_ratio = abs(target1 - entry) / abs(entry - stop_loss)
        alert_msg += f"\n💡 *Risk-Reward:* 1:{rr_ratio:.2f}"
    
    send_message(chat_id, alert_msg)
    logging.info("Sent %s alert for %s to user %s (entry=%.2f, sl=%.2f, t1=%.2f)", 
                signal, symbol, chat_id, entry, stop_loss, target1)
    
    return True


def run_once():
    """Run alert check once for all subscribers."""
    if not is_market_open():
        return
    
    subs = list_subscribers()
    if not subs:
        logging.info("No subscribers, skipping")
        return
    
    for symbol_name in WATCHLIST:
        symbol = symbol_name.strip().upper()
        if symbol not in TICKER_MAP:
            continue
        
        ticker, name = TICKER_MAP[symbol]
        
        try:
            # Get AI analysis for latest 2-min candle
            analysis = analyze_index(ticker, name)
            
            # Send to all subscribers
            for chat_id in subs:
                try:
                    generate_trading_alert(symbol, analysis, chat_id)
                except Exception as e:
                    logging.exception("Failed alert for user %s: %s", chat_id, e)
                    
        except Exception as e:
            logging.exception("Failed analysis for %s: %s", symbol, e)


def run_loop():
    """Main alerter loop - runs only during market hours."""
    logging.info("Starting real-time alerter for %s (market hours only)", WATCHLIST)
    
    while True:
        try:
            if is_market_open():
                start = time.time()
                run_once()
                elapsed = time.time() - start
                sleep_for = max(1, INTERVAL - elapsed)
                time.sleep(sleep_for)
            else:
                # Wait for market to open
                now = datetime.now(IST)
                hours_until_open = (24 - now.hour) if now.hour >= MARKET_CLOSE_HOUR else (MARKET_OPEN_HOUR - now.hour)
                logging.info("Market closed (next open in ~%d hours). Sleeping.", hours_until_open)
                time.sleep(60)
        except Exception as e:
            logging.exception("Error in alerter loop: %s", e)
            time.sleep(10)


if __name__ == "__main__":
    run_loop()




if __name__ == "__main__":
    run_loop()
