"""
Real-time intraday candle snapshot scheduler for NIFTY/SENSEX.
Runs only during IST market hours (9:30 AM - 3:30 PM IST Mon-Fri).
Fetches 2-minute candles and stores for AI analysis.
"""

import os
import time
import signal
import sys
import logging
from datetime import datetime, timedelta
import pytz
from candle_analyzer import fetch_index_candles

IST = pytz.timezone('Asia/Kolkata')
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MIN = 30
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MIN = 30

WATCHLIST = os.environ.get("WATCHLIST", "NIFTY,SENSEX").split(",")
INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_INTERVAL", "120"))  # Check every 2 min

# Symbol to ticker mapping
TICKER_MAP = {
    "NIFTY": "^NSEI",
    "SENSEX": "^BSESN",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def is_market_open() -> bool:
    """Check if NSE market is open (9:30 AM - 3:30 PM IST, Mon-Fri)."""
    now = datetime.now(IST)
    
    # Check if weekday (0=Mon, 6=Sun)
    if now.weekday() >= 5:
        return False
    
    # Check market hours
    market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0)
    market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def snapshot_once():
    """Fetch latest 2-day intraday candles and save."""
    if not is_market_open():
        logging.info("Market closed, skipping snapshot")
        return
    
    for symbol_name in WATCHLIST:
        symbol = symbol_name.strip().upper()
        if symbol not in TICKER_MAP:
            logging.warning("Symbol %s not in mapping (use NIFTY or SENSEX)", symbol)
            continue
        
        ticker = TICKER_MAP[symbol]
        try:
            # Fetch 2-minute candlesticks for last 5 days
            df = fetch_index_candles(ticker, period="5d", interval="2m")
            if df is None or df.empty:
                logging.warning("No candle data for %s", symbol)
                continue
            
            # Store just for logging; real analysis happens in alerter
            latest_close = float(df['Close'].iloc[-1])
            latest_high = float(df['High'].iloc[-1])
            latest_low = float(df['Low'].iloc[-1])
            
            logging.info(
                "Snapshot %s: Price=%.2f High=%.2f Low=%.2f Candles=%d",
                symbol, latest_close, latest_high, latest_low, len(df)
            )
        except Exception as e:
            logging.exception("Snapshot failed for %s: %s", symbol, e)


def run_loop():
    """Main scheduler loop - runs only during market hours."""
    logging.info("Starting intraday scheduler for %s every %d seconds (market hours only)", WATCHLIST, INTERVAL_SECONDS)
    
    while True:
        try:
            if is_market_open():
                start = time.time()
                snapshot_once()
                elapsed = time.time() - start
                sleep_for = max(1, INTERVAL_SECONDS - elapsed)
                logging.debug("Sleeping for %.1f seconds", sleep_for)
                time.sleep(sleep_for)
            else:
                # Market closed, sleep longer
                logging.info("Market hours: %.2f (waiting for 9:30 AM IST)", 
                            (datetime.now(IST).hour + datetime.now(IST).minute / 60))
                time.sleep(60)  # Check again in 1 minute
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.exception("Error in scheduler loop: %s", e)
            time.sleep(5)


def _signal_handler(sig, frame):
    logging.info("Scheduler stopping")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    run_loop()



if __name__ == "__main__":
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    run_loop()
