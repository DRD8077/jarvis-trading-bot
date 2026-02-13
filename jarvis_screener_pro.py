"""
🔍⚡ JARVIS SCREENER PRO — Natural Language Stock Screener
═══════════════════════════════════════════════════════════════════
"RSI 30 ke neeche stocks dikhao" → Instant Screened Results
"Volume breakout with RSI oversold" → Smart Multi-filter Screener

Features:
  • Natural language screening: "oversold stocks with high volume"
  • RSI screener (overbought/oversold)
  • Volume breakout detection (2x+ avg volume)
  • 52-week high/low proximity
  • SMA/EMA crossover detection
  • Gap-up/Gap-down scanner
  • VWAP breakout detection
  • Momentum screener (biggest movers)
  • Sector-wise scanning
  • NIFTY 50 + NIFTY Next 50 universe

Author: JARVIS AI (Boss: Deepak Kumar)
"""

import os
import re
import time
import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

logger = logging.getLogger("jarvis_screener")

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

SCREENER_AVAILABLE = YF_AVAILABLE

# ═══════════════════════════════════════════════════════════
#  STOCK UNIVERSE
# ═══════════════════════════════════════════════════════════
NIFTY50_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL",
    "ITC", "SBIN", "LT", "BAJFINANCE", "HCLTECH", "MARUTI",
    "KOTAKBANK", "TATAMOTORS", "AXISBANK", "SUNPHARMA", "TITAN",
    "ADANIENT", "WIPRO", "TECHM", "NTPC", "POWERGRID",
    "ULTRACEMCO", "ASIANPAINT", "HINDUNILVR", "M&M", "TATASTEEL",
    "ONGC", "COALINDIA", "JSWSTEEL", "NESTLEIND", "BAJAJFINSV",
    "BRITANNIA", "CIPLA", "DRREDDY", "APOLLOHOSP", "GRASIM",
    "BPCL", "HEROMOTOCO", "EICHERMOT", "TATACONSUM", "DIVISLAB",
    "INDUSINDBK", "SBILIFE", "HDFCLIFE", "ADANIPORTS", "BAJAJ-AUTO",
    "TRENT", "BEL", "HAL",
]

NIFTY_NEXT50 = [
    "ZOMATO", "IRCTC", "PAYTM", "DELHIVERY", "NYKAA",
    "POLYCAB", "PIIND", "SIEMENS", "ABB", "HAVELLS",
    "GODREJCP", "COLPAL", "MARICO", "DABUR", "PAGEIND",
    "MUTHOOTFIN", "CHOLAFIN", "SHRIRAMFIN", "MFSL", "ICICIGI",
    "SBICARD", "PNB", "BANKBARODA", "CANBK", "IDFCFIRSTB",
    "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD",
    "LODHA", "PERSISTENT", "LTIM", "COFORGE", "MPHASIS",
    "TATAPOWER", "NHPC", "IREDA", "PFC", "RECLTD",
]

ALL_SCREENER_STOCKS = NIFTY50_STOCKS + NIFTY_NEXT50

# Cache for stock data
_data_cache: Dict[str, Tuple[float, pd.DataFrame]] = {}
CACHE_TTL = 300  # 5 minutes


def _get_yf_symbol(stock: str) -> str:
    """Convert to yfinance symbol"""
    if stock == "M&M":
        return "M%26M.NS"
    return f"{stock}.NS"


def _fetch_stock_data(stock: str, period: str = "3mo") -> Optional[pd.DataFrame]:
    """Fetch with caching"""
    cache_key = f"{stock}_{period}"
    now = time.time()
    
    if cache_key in _data_cache:
        ts, data = _data_cache[cache_key]
        if now - ts < CACHE_TTL:
            return data
    
    try:
        ticker = _get_yf_symbol(stock)
        data = yf.download(ticker, period=period, interval="1d", progress=False)
        if data is not None and not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            _data_cache[cache_key] = (now, data)
            return data
    except Exception:
        pass
    return None


def _batch_fetch(stocks: List[str], period: str = "3mo") -> Dict[str, pd.DataFrame]:
    """Parallel fetch for multiple stocks"""
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {executor.submit(_fetch_stock_data, s, period): s for s in stocks}
        for future in as_completed(future_map):
            stock = future_map[future]
            try:
                data = future.result()
                if data is not None and not data.empty:
                    results[stock] = data
            except Exception:
                pass
    return results


# ═══════════════════════════════════════════════════════════
#  SCREEN FUNCTIONS
# ═══════════════════════════════════════════════════════════
def _calc_rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    val = rsi.iloc[-1]
    return float(val) if not pd.isna(val) else 50.0


def _analyze_stock(stock: str, data: pd.DataFrame) -> Dict[str, Any]:
    """Complete analysis for one stock"""
    if len(data) < 20:
        return {}
    
    close = float(data['Close'].iloc[-1])
    prev_close = float(data['Close'].iloc[-2])
    change_pct = ((close - prev_close) / prev_close) * 100
    
    vol = float(data['Volume'].iloc[-1])
    avg_vol = float(data['Volume'].tail(20).mean())
    vol_ratio = vol / avg_vol if avg_vol > 0 else 1
    
    rsi = _calc_rsi(data['Close'])
    
    sma20 = float(data['Close'].rolling(20).mean().iloc[-1])
    sma50 = float(data['Close'].rolling(50).mean().iloc[-1]) if len(data) >= 50 else close
    sma200 = float(data['Close'].rolling(200).mean().iloc[-1]) if len(data) >= 200 else close
    
    ema9 = float(data['Close'].ewm(span=9).mean().iloc[-1])
    ema21 = float(data['Close'].ewm(span=21).mean().iloc[-1])
    
    high_52w = float(data['High'].tail(252).max()) if len(data) >= 50 else float(data['High'].max())
    low_52w = float(data['Low'].tail(252).min()) if len(data) >= 50 else float(data['Low'].min())
    
    # Gap detection
    prev_high = float(data['High'].iloc[-2])
    prev_low = float(data['Low'].iloc[-2])
    today_open = float(data['Open'].iloc[-1])
    gap_up = today_open > prev_high
    gap_down = today_open < prev_low
    gap_pct = ((today_open - prev_close) / prev_close) * 100
    
    # VWAP
    typical = (data['High'] + data['Low'] + data['Close']) / 3
    cum_vol = data['Volume'].cumsum()
    vwap = float((typical * data['Volume']).cumsum().iloc[-1] / cum_vol.iloc[-1]) if cum_vol.iloc[-1] > 0 else close
    
    # MACD
    ema12 = data['Close'].ewm(span=12).mean()
    ema26 = data['Close'].ewm(span=26).mean()
    macd = float((ema12 - ema26).iloc[-1])
    macd_signal = float((ema12 - ema26).ewm(span=9).mean().iloc[-1])
    
    # Momentum (5-day, 20-day)
    mom5 = ((close - float(data['Close'].iloc[-6])) / float(data['Close'].iloc[-6])) * 100 if len(data) > 6 else 0
    mom20 = ((close - float(data['Close'].iloc[-21])) / float(data['Close'].iloc[-21])) * 100 if len(data) > 21 else 0
    
    # Bollinger position
    bb_sma = float(data['Close'].rolling(20).mean().iloc[-1])
    bb_std = float(data['Close'].rolling(20).std().iloc[-1])
    bb_upper = bb_sma + 2 * bb_std
    bb_lower = bb_sma - 2 * bb_std
    bb_pct = (close - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
    
    return {
        "stock": stock,
        "close": close,
        "change_pct": change_pct,
        "volume": vol,
        "avg_volume": avg_vol,
        "vol_ratio": vol_ratio,
        "rsi": rsi,
        "sma20": sma20,
        "sma50": sma50,
        "sma200": sma200,
        "ema9": ema9,
        "ema21": ema21,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "near_52w_high": close >= high_52w * 0.97,
        "near_52w_low": close <= low_52w * 1.03,
        "gap_up": gap_up,
        "gap_down": gap_down,
        "gap_pct": gap_pct,
        "vwap": vwap,
        "above_vwap": close > vwap,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_bullish": macd > macd_signal,
        "mom5": mom5,
        "mom20": mom20,
        "bb_pct": bb_pct,
        "above_sma20": close > sma20,
        "above_sma50": close > sma50,
        "above_sma200": close > sma200,
        "golden_cross": ema9 > ema21 and float(data['Close'].ewm(span=9).mean().iloc[-2]) <= float(data['Close'].ewm(span=21).mean().iloc[-2]),
        "death_cross": ema9 < ema21 and float(data['Close'].ewm(span=9).mean().iloc[-2]) >= float(data['Close'].ewm(span=21).mean().iloc[-2]),
    }


# ═══════════════════════════════════════════════════════════
#  SCREENER FILTERS
# ═══════════════════════════════════════════════════════════
def screen_rsi_oversold(analyses: List[Dict], threshold: float = 30) -> List[Dict]:
    return sorted([a for a in analyses if a.get("rsi", 50) < threshold], key=lambda x: x["rsi"])


def screen_rsi_overbought(analyses: List[Dict], threshold: float = 70) -> List[Dict]:
    return sorted([a for a in analyses if a.get("rsi", 50) > threshold], key=lambda x: -x["rsi"])


def screen_volume_breakout(analyses: List[Dict], min_ratio: float = 2.0) -> List[Dict]:
    return sorted([a for a in analyses if a.get("vol_ratio", 0) >= min_ratio], key=lambda x: -x["vol_ratio"])


def screen_gap_up(analyses: List[Dict]) -> List[Dict]:
    return sorted([a for a in analyses if a.get("gap_up")], key=lambda x: -x["gap_pct"])


def screen_gap_down(analyses: List[Dict]) -> List[Dict]:
    return sorted([a for a in analyses if a.get("gap_down")], key=lambda x: x["gap_pct"])


def screen_52w_high(analyses: List[Dict]) -> List[Dict]:
    return [a for a in analyses if a.get("near_52w_high")]


def screen_52w_low(analyses: List[Dict]) -> List[Dict]:
    return [a for a in analyses if a.get("near_52w_low")]


def screen_golden_cross(analyses: List[Dict]) -> List[Dict]:
    return [a for a in analyses if a.get("golden_cross")]


def screen_death_cross(analyses: List[Dict]) -> List[Dict]:
    return [a for a in analyses if a.get("death_cross")]


def screen_momentum_top(analyses: List[Dict], n: int = 10) -> List[Dict]:
    return sorted(analyses, key=lambda x: -x.get("mom5", 0))[:n]


def screen_momentum_bottom(analyses: List[Dict], n: int = 10) -> List[Dict]:
    return sorted(analyses, key=lambda x: x.get("mom5", 0))[:n]


def screen_above_vwap(analyses: List[Dict]) -> List[Dict]:
    return [a for a in analyses if a.get("above_vwap")]


def screen_below_bollinger(analyses: List[Dict]) -> List[Dict]:
    return sorted([a for a in analyses if a.get("bb_pct", 0.5) < 0.1], key=lambda x: x["bb_pct"])


def screen_macd_bullish(analyses: List[Dict]) -> List[Dict]:
    return [a for a in analyses if a.get("macd_bullish")]


def screen_trend_strong_bull(analyses: List[Dict]) -> List[Dict]:
    """Price above SMA20, SMA50, SMA200 + RSI 50-70 + MACD bullish"""
    return [a for a in analyses if 
            a.get("above_sma20") and a.get("above_sma50") and a.get("above_sma200") and
            50 < a.get("rsi", 0) < 70 and a.get("macd_bullish")]


# ═══════════════════════════════════════════════════════════
#  NLU — PARSE SCREENER QUERY
# ═══════════════════════════════════════════════════════════
def parse_screener_query(text: str) -> Dict[str, Any]:
    """
    Parse natural language screener request.
    
    Examples:
        "RSI 30 ke neeche stocks" → rsi_oversold
        "volume breakout stocks" → volume_breakout
        "52 week high ke paas" → 52w_high
        "gap up stocks today" → gap_up
        "strong bullish stocks" → trend_strong_bull
        "top momentum stocks" → momentum_top
    """
    text_lower = text.lower()
    
    filters = []
    
    # RSI
    if re.search(r'rsi.*(oversold|neeche|below|under|low|kam|<\s*30)', text_lower):
        threshold = 30
        m = re.search(r'rsi.*?(\d+)', text_lower)
        if m:
            threshold = float(m.group(1))
        filters.append(("rsi_oversold", threshold))
    elif re.search(r'rsi.*(overbought|upar|above|over|high|zyada|>\s*70)', text_lower):
        threshold = 70
        m = re.search(r'rsi.*?(\d+)', text_lower)
        if m:
            threshold = float(m.group(1))
        filters.append(("rsi_overbought", threshold))
    elif re.search(r'oversold', text_lower):
        filters.append(("rsi_oversold", 30))
    elif re.search(r'overbought', text_lower):
        filters.append(("rsi_overbought", 70))
    
    # Volume
    if re.search(r'volume.*(breakout|spike|high|zyada|heavy|explosion|2x|3x)', text_lower):
        ratio = 2.0
        m = re.search(r'(\d+)x', text_lower)
        if m:
            ratio = float(m.group(1))
        filters.append(("volume_breakout", ratio))
    
    # Gap
    if re.search(r'gap\s*up', text_lower):
        filters.append(("gap_up", None))
    if re.search(r'gap\s*down', text_lower):
        filters.append(("gap_down", None))
    
    # 52 week
    if re.search(r'52\s*w.*(high|upar|top)', text_lower):
        filters.append(("52w_high", None))
    if re.search(r'52\s*w.*(low|neeche|bottom)', text_lower):
        filters.append(("52w_low", None))
    
    # Crossover
    if re.search(r'golden\s*cross', text_lower):
        filters.append(("golden_cross", None))
    if re.search(r'death\s*cross', text_lower):
        filters.append(("death_cross", None))
    
    # Momentum
    if re.search(r'(momentum|top\s*gainer|biggest\s*mover|top\s*mover)', text_lower):
        filters.append(("momentum_top", 10))
    if re.search(r'(biggest\s*loser|top\s*loser|worst|laggard)', text_lower):
        filters.append(("momentum_bottom", 10))
    
    # VWAP
    if re.search(r'(vwap|above\s*vwap)', text_lower):
        filters.append(("above_vwap", None))
    
    # Bollinger
    if re.search(r'(bollinger.*low|below.*bollinger|bb.*oversold)', text_lower):
        filters.append(("below_bollinger", None))
    
    # MACD
    if re.search(r'macd.*(bull|buy|positive|cross)', text_lower):
        filters.append(("macd_bullish", None))
    
    # Strong bullish
    if re.search(r'(strong\s*bull|super\s*bull|trending\s*up|strong\s*trend)', text_lower):
        filters.append(("trend_strong_bull", None))
    
    # Default: just show top momentum if nothing matched
    if not filters:
        filters.append(("momentum_top", 10))
    
    return {"filters": filters}


# ═══════════════════════════════════════════════════════════
#  MAIN SCREENER
# ═══════════════════════════════════════════════════════════
def run_screener(text: str = "", stocks: List[str] = None) -> str:
    """
    Main entry point — run screener and return formatted results.
    """
    if not SCREENER_AVAILABLE:
        return "❌ Screener unavailable — yfinance not installed"
    
    if stocks is None:
        stocks = NIFTY50_STOCKS
    
    # Parse query
    parsed = parse_screener_query(text)
    filters = parsed["filters"]
    
    # Fetch data
    logger.info(f"[SCREENER] Fetching data for {len(stocks)} stocks...")
    all_data = _batch_fetch(stocks)
    
    if not all_data:
        return "❌ Data fetch failed — try again in a minute"
    
    # Analyze all stocks
    analyses = []
    for stock, data in all_data.items():
        try:
            a = _analyze_stock(stock, data)
            if a:
                analyses.append(a)
        except Exception as e:
            logger.debug(f"[SCREENER] Error analyzing {stock}: {e}")
    
    if not analyses:
        return "❌ No stocks could be analyzed"
    
    # Apply filters
    results = analyses
    filter_labels = []
    
    for filter_name, param in filters:
        if filter_name == "rsi_oversold":
            results = screen_rsi_oversold(results, param)
            filter_labels.append(f"RSI < {param}")
        elif filter_name == "rsi_overbought":
            results = screen_rsi_overbought(results, param)
            filter_labels.append(f"RSI > {param}")
        elif filter_name == "volume_breakout":
            results = screen_volume_breakout(results, param)
            filter_labels.append(f"Volume {param}x+")
        elif filter_name == "gap_up":
            results = screen_gap_up(results)
            filter_labels.append("Gap Up")
        elif filter_name == "gap_down":
            results = screen_gap_down(results)
            filter_labels.append("Gap Down")
        elif filter_name == "52w_high":
            results = screen_52w_high(results)
            filter_labels.append("Near 52W High")
        elif filter_name == "52w_low":
            results = screen_52w_low(results)
            filter_labels.append("Near 52W Low")
        elif filter_name == "golden_cross":
            results = screen_golden_cross(results)
            filter_labels.append("Golden Cross")
        elif filter_name == "death_cross":
            results = screen_death_cross(results)
            filter_labels.append("Death Cross")
        elif filter_name == "momentum_top":
            results = screen_momentum_top(results, param)
            filter_labels.append(f"Top {param} Momentum")
        elif filter_name == "momentum_bottom":
            results = screen_momentum_bottom(results, param)
            filter_labels.append(f"Bottom {param} Momentum")
        elif filter_name == "above_vwap":
            results = screen_above_vwap(results)
            filter_labels.append("Above VWAP")
        elif filter_name == "below_bollinger":
            results = screen_below_bollinger(results)
            filter_labels.append("Below Bollinger Lower")
        elif filter_name == "macd_bullish":
            results = screen_macd_bullish(results)
            filter_labels.append("MACD Bullish")
        elif filter_name == "trend_strong_bull":
            results = screen_trend_strong_bull(results)
            filter_labels.append("Strong Bullish Trend")
    
    # Format output
    filter_str = " + ".join(filter_labels) if filter_labels else "All Stocks"
    
    output = (
        f"🔍 *JARVIS SCREENER PRO*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 *Filter:* {filter_str}\n"
        f"📊 *Universe:* {len(analyses)} stocks scanned\n"
        f"✅ *Results:* {len(results)} stocks matched\n\n"
    )
    
    if not results:
        output += "❌ Koi stock is filter mein nahi aaya.\n"
        output += "💡 _Try broader filters or different criteria_"
        return output
    
    # Top 15 results
    for i, r in enumerate(results[:15], 1):
        emoji = "🟢" if r["change_pct"] >= 0 else "🔴"
        vol_tag = "🔥" if r["vol_ratio"] > 2 else ""
        rsi_tag = ""
        if r["rsi"] < 30:
            rsi_tag = "💚OVS"
        elif r["rsi"] > 70:
            rsi_tag = "🔴OVB"
        
        output += (
            f"*{i}. {r['stock']}* — ₹{r['close']:,.2f} {emoji} {r['change_pct']:+.1f}%\n"
            f"   RSI: {r['rsi']:.0f}{rsi_tag} | Vol: {r['vol_ratio']:.1f}x{vol_tag}"
            f" | Mom5d: {r['mom5']:+.1f}%\n"
        )
    
    if len(results) > 15:
        output += f"\n_...and {len(results)-15} more stocks_\n"
    
    output += f"\n⏰ _Screened at {datetime.now().strftime('%H:%M:%S IST')}_"
    
    return output


# ═══════════════════════════════════════════════════════════
#  QUICK SCREENERS (Pre-built)
# ═══════════════════════════════════════════════════════════
def screen_oversold() -> str:
    return run_screener("RSI oversold below 30")

def screen_overbought() -> str:
    return run_screener("RSI overbought above 70")

def screen_volume_spike() -> str:
    return run_screener("volume breakout 2x")

def screen_gap_ups() -> str:
    return run_screener("gap up stocks")

def screen_top_momentum() -> str:
    return run_screener("top momentum stocks")

def screen_52week_high() -> str:
    return run_screener("52 week high stocks")

def screen_strong_bullish() -> str:
    return run_screener("strong bullish trend stocks")


if __name__ == "__main__":
    print(run_screener("RSI 30 ke neeche oversold stocks dikhao"))
