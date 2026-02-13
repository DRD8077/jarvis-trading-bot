"""
📊⚡ JARVIS CHART ENGINE — Professional Trading Charts in Telegram
═══════════════════════════════════════════════════════════════════
Live Candlestick Charts → Technical Indicators → Support/Resistance → Telegram Photo

"RELIANCE chart dikhao" → Instant Professional Candlestick Chart
"NIFTY 1hr chart with RSI" → Multi-indicator chart as image

Features:
  • Professional candlestick charts (mplfinance)
  • SMA/EMA overlays (9, 21, 50, 200)
  • RSI subplot with overbought/oversold zones
  • MACD subplot with signal line + histogram
  • Bollinger Bands overlay
  • VWAP line
  • Volume bars with color coding
  • Auto-detect support/resistance levels
  • Multiple timeframes: 1min, 5min, 15min, 1hr, daily, weekly
  • Dark theme (pro trader look)
  • Chart saved as PNG → ready for Telegram

Author: JARVIS AI (Boss: Deepak Kumar)
"""

import os
import io
import logging
import tempfile
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger("jarvis_chart_engine")

# ═══════════════════════════════════════════════════════════
#  IMPORTS — mplfinance + matplotlib
# ═══════════════════════════════════════════════════════════
try:
    import mplfinance as mpf
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    CHART_ENGINE_AVAILABLE = True
    logger.info("[CHART-ENGINE] 📊 Chart Engine loaded — Professional Trading Charts ACTIVE")
except ImportError as e:
    CHART_ENGINE_AVAILABLE = False
    logger.warning(f"[CHART-ENGINE] Chart libraries not available: {e}")

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
CHART_DIR = os.path.join(os.path.dirname(__file__), "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# NSE symbol mapping
NSE_SYMBOL_MAP = {
    "NIFTY": "^NSEI", "NIFTY50": "^NSEI", "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK", "BANK NIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS", "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS", "TATAMOTORS": "TATAMOTORS.NS",
    "TATASTEEL": "TATASTEEL.NS", "ITC": "ITC.NS",
    "WIPRO": "WIPRO.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "MARUTI": "MARUTI.NS", "HCLTECH": "HCLTECH.NS",
    "LT": "LT.NS", "AXISBANK": "AXISBANK.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "ADANIENT": "ADANIENT.NS",
    "ADANIPORTS": "ADANIPORTS.NS", "BHARTIARTL": "BHARTIARTL.NS",
    "SUNPHARMA": "SUNPHARMA.NS", "TITAN": "TITAN.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS", "ASIANPAINT": "ASIANPAINT.NS",
    "HINDUNILVR": "HINDUNILVR.NS", "M&M": "M%26M.NS",
    "TECHM": "TECHM.NS", "POWERGRID": "POWERGRID.NS",
    "NTPC": "NTPC.NS", "COALINDIA": "COALINDIA.NS",
    "ONGC": "ONGC.NS", "JSWSTEEL": "JSWSTEEL.NS",
    "DRREDDY": "DRREDDY.NS", "CIPLA": "CIPLA.NS",
    "HEROMOTOCO": "HEROMOTOCO.NS", "BPCL": "BPCL.NS",
    "GRASIM": "GRASIM.NS", "DIVISLAB": "DIVISLAB.NS",
    "INDUSINDBK": "INDUSINDBK.NS", "EICHERMOT": "EICHERMOT.NS",
    "APOLLOHOSP": "APOLLOHOSP.NS", "TATACONSUM": "TATACONSUM.NS",
    "SBILIFE": "SBILIFE.NS", "HDFCLIFE": "HDFCLIFE.NS",
    "BRITANNIA": "BRITANNIA.NS", "NESTLEIND": "NESTLEIND.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS", "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
    "BIOCON": "BIOCON.NS", "HAL": "HAL.NS",
    "IRCTC": "IRCTC.NS", "ZOMATO": "ZOMATO.NS",
    "PAYTM": "PAYTM.NS",
    # Crypto
    "BTC": "BTC-USD", "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD", "ETHEREUM": "ETH-USD",
    "SOL": "SOL-USD", "SOLANA": "SOL-USD",
    "BNB": "BNB-USD", "XRP": "XRP-USD",
    "DOGE": "DOGE-USD", "ADA": "ADA-USD",
}

# Timeframe mapping for yfinance
TIMEFRAME_MAP = {
    "1m": ("1m", "1d"), "1min": ("1m", "1d"),
    "5m": ("5m", "5d"), "5min": ("5m", "5d"),
    "15m": ("15m", "5d"), "15min": ("15m", "5d"),
    "30m": ("30m", "10d"), "30min": ("30m", "10d"),
    "1h": ("1h", "30d"), "1hr": ("1h", "30d"), "hourly": ("1h", "30d"),
    "1d": ("1d", "6mo"), "daily": ("1d", "6mo"), "day": ("1d", "6mo"),
    "1wk": ("1wk", "2y"), "weekly": ("1wk", "2y"), "week": ("1wk", "2y"),
    "1mo": ("1mo", "5y"), "monthly": ("1mo", "5y"),
}

# ═══════════════════════════════════════════════════════════
#  DARK THEME STYLE
# ═══════════════════════════════════════════════════════════
JARVIS_DARK_STYLE = {
    "base_mpf_style": "nightclouds",
    "marketcolors": None,  # Will be set dynamically
    "facecolor": "#0e1117",
    "edgecolor": "#1a1a2e",
    "figcolor": "#0e1117",
    "gridcolor": "#1e2a3a",
    "gridstyle": "--",
    "gridaxis": "both",
}


def _get_jarvis_style():
    """Create professional dark theme for charts"""
    mc = mpf.make_marketcolors(
        up='#00ff88', down='#ff3366',
        edge={'up': '#00ff88', 'down': '#ff3366'},
        wick={'up': '#00ff88', 'down': '#ff3366'},
        volume={'up': '#00ff8855', 'down': '#ff336655'},
        ohlc='i'
    )
    return mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        marketcolors=mc,
        facecolor='#0e1117',
        edgecolor='#0e1117',
        figcolor='#0e1117',
        gridcolor='#1e2a3a',
        gridstyle='--',
        y_on_right=True,
        rc={
            'axes.labelcolor': '#ffffff',
            'xtick.color': '#888888',
            'ytick.color': '#888888',
            'font.size': 9,
            'axes.titlesize': 12,
        }
    )


# ═══════════════════════════════════════════════════════════
#  DATA FETCHER
# ═══════════════════════════════════════════════════════════
def _resolve_symbol(symbol: str) -> str:
    """Resolve user symbol to yfinance ticker"""
    clean = symbol.strip().upper().replace(" ", "")
    if clean in NSE_SYMBOL_MAP:
        return NSE_SYMBOL_MAP[clean]
    # Try adding .NS for Indian stocks
    if not any(c in clean for c in ['.', '-', '^']):
        return f"{clean}.NS"
    return clean


def fetch_chart_data(symbol: str, timeframe: str = "1d") -> Optional[pd.DataFrame]:
    """Fetch OHLCV data for charting"""
    if not YFINANCE_AVAILABLE:
        return None
    
    ticker = _resolve_symbol(symbol)
    tf_info = TIMEFRAME_MAP.get(timeframe.lower(), ("1d", "6mo"))
    interval, period = tf_info
    
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if data is None or data.empty:
            return None
        
        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Ensure required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required:
            if col not in data.columns:
                return None
        
        # Drop NaN rows
        data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        if len(data) < 5:
            return None
            
        return data
        
    except Exception as e:
        logger.error(f"[CHART-ENGINE] Data fetch error for {ticker}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════════
def _calc_sma(data: pd.DataFrame, period: int) -> pd.Series:
    return data['Close'].rolling(window=period).mean()


def _calc_ema(data: pd.DataFrame, period: int) -> pd.Series:
    return data['Close'].ewm(span=period, adjust=False).mean()


def _calc_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _calc_macd(data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal
    return macd_line, signal, histogram


def _calc_bollinger(data: pd.DataFrame, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return upper, sma, lower


def _calc_vwap(data: pd.DataFrame) -> pd.Series:
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    cum_vol = data['Volume'].cumsum()
    cum_vol_price = (typical_price * data['Volume']).cumsum()
    return cum_vol_price / cum_vol.replace(0, np.nan)


def _find_support_resistance(data: pd.DataFrame, window: int = 10) -> Tuple[List[float], List[float]]:
    """Find support and resistance levels using pivot points"""
    supports = []
    resistances = []
    
    highs = data['High'].values
    lows = data['Low'].values
    
    for i in range(window, len(data) - window):
        # Resistance: local maximum
        if highs[i] == max(highs[i-window:i+window+1]):
            resistances.append(float(highs[i]))
        # Support: local minimum
        if lows[i] == min(lows[i-window:i+window+1]):
            supports.append(float(lows[i]))
    
    # Deduplicate close levels (within 0.5%)
    supports = _deduplicate_levels(supports)
    resistances = _deduplicate_levels(resistances)
    
    return supports[-3:], resistances[-3:]  # Last 3 each


def _deduplicate_levels(levels: List[float], threshold: float = 0.005) -> List[float]:
    """Remove duplicate levels within threshold"""
    if not levels:
        return levels
    levels.sort()
    deduped = [levels[0]]
    for l in levels[1:]:
        if abs(l - deduped[-1]) / max(deduped[-1], 0.01) > threshold:
            deduped.append(l)
    return deduped


# ═══════════════════════════════════════════════════════════
#  CHART GENERATOR — THE MAIN ENGINE
# ═══════════════════════════════════════════════════════════
def generate_chart(
    symbol: str,
    timeframe: str = "daily",
    indicators: List[str] = None,
    show_sr: bool = True,
    last_n: int = 100
) -> Optional[str]:
    """
    Generate professional trading chart as PNG file.
    
    Args:
        symbol: Stock/crypto symbol (RELIANCE, NIFTY, BTC, etc.)
        timeframe: 1m/5m/15m/1h/daily/weekly
        indicators: List of indicators ['sma', 'ema', 'rsi', 'macd', 'bb', 'vwap', 'volume']
        show_sr: Show support/resistance lines
        last_n: Number of candles to show
        
    Returns:
        Path to PNG file, or None on failure
    """
    if not CHART_ENGINE_AVAILABLE:
        return None
    
    if indicators is None:
        indicators = ['sma', 'ema', 'rsi', 'macd', 'volume']
    
    # Fetch data
    data = fetch_chart_data(symbol, timeframe)
    if data is None:
        logger.warning(f"[CHART-ENGINE] No data for {symbol}")
        return None
    
    # Trim to last_n candles
    if len(data) > last_n:
        data = data.tail(last_n).copy()
    
    # Get style
    style = _get_jarvis_style()
    
    # Build additional plots
    addplots = []
    panel_count = 0  # 0 = main chart
    
    # ── SMA / EMA overlays on main panel ──
    if 'sma' in indicators:
        for period, color in [(9, '#ffff00'), (21, '#ff9900'), (50, '#00aaff'), (200, '#ff00ff')]:
            if len(data) > period:
                sma = _calc_sma(data, period)
                addplots.append(mpf.make_addplot(
                    sma, panel=0, color=color, width=0.8,
                    linestyle='-', secondary_y=False
                ))
    
    if 'ema' in indicators:
        for period, color in [(9, '#00ffcc'), (21, '#ff6600')]:
            if len(data) > period:
                ema = _calc_ema(data, period)
                addplots.append(mpf.make_addplot(
                    ema, panel=0, color=color, width=1.0,
                    linestyle='--', secondary_y=False
                ))
    
    # ── Bollinger Bands on main panel ──
    if 'bb' in indicators and len(data) > 20:
        upper, mid, lower = _calc_bollinger(data)
        addplots.append(mpf.make_addplot(upper, panel=0, color='#4488ff44', width=0.6))
        addplots.append(mpf.make_addplot(mid, panel=0, color='#4488ff', width=0.5, linestyle='--'))
        addplots.append(mpf.make_addplot(lower, panel=0, color='#4488ff44', width=0.6))
    
    # ── VWAP on main panel ──
    if 'vwap' in indicators:
        vwap = _calc_vwap(data)
        addplots.append(mpf.make_addplot(
            vwap, panel=0, color='#ff00ff', width=1.0, linestyle=':'
        ))
    
    # ── RSI subplot ──
    rsi_panel = None
    if 'rsi' in indicators and len(data) > 14:
        panel_count += 1
        rsi_panel = panel_count + 1  # mplfinance volume takes panel 1
        rsi = _calc_rsi(data)
        addplots.append(mpf.make_addplot(rsi, panel=rsi_panel, color='#ffaa00', width=1.0, ylabel='RSI'))
        # Overbought/oversold levels
        addplots.append(mpf.make_addplot(
            pd.Series([70]*len(data), index=data.index), panel=rsi_panel, 
            color='#ff336688', width=0.5, linestyle='--'
        ))
        addplots.append(mpf.make_addplot(
            pd.Series([30]*len(data), index=data.index), panel=rsi_panel,
            color='#00ff8888', width=0.5, linestyle='--'
        ))
    
    # ── MACD subplot ──
    if 'macd' in indicators and len(data) > 26:
        panel_count += 1
        macd_panel = rsi_panel + 1 if rsi_panel else panel_count + 1
        macd_line, signal, histogram = _calc_macd(data)
        
        # Color histogram
        hist_colors = ['#00ff88' if v >= 0 else '#ff3366' for v in histogram.values]
        
        addplots.append(mpf.make_addplot(macd_line, panel=macd_panel, color='#00aaff', width=0.8, ylabel='MACD'))
        addplots.append(mpf.make_addplot(signal, panel=macd_panel, color='#ff6600', width=0.8))
        addplots.append(mpf.make_addplot(histogram, panel=macd_panel, type='bar', color=hist_colors, width=0.5))
    
    # ── Generate chart ──
    try:
        # Build title
        clean_sym = symbol.strip().upper()
        tf_display = timeframe.upper()
        current_price = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price
        change_pct = ((current_price - prev_close) / prev_close) * 100
        change_emoji = "🟢" if change_pct >= 0 else "🔴"
        
        title = f"📊 {clean_sym} | {tf_display} | ₹{current_price:,.2f} {change_emoji} {change_pct:+.2f}%"
        
        # Chart output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(CHART_DIR, f"chart_{clean_sym}_{timestamp}.png")
        
        # Panel ratios
        panel_ratios = [4, 1]  # Main + Volume
        if rsi_panel:
            panel_ratios.append(1.2)
        if 'macd' in indicators and len(data) > 26:
            panel_ratios.append(1.2)
        
        # Generate
        fig, axes = mpf.plot(
            data,
            type='candle',
            style=style,
            title=title,
            volume='volume' in indicators,
            addplot=addplots if addplots else None,
            figsize=(14, 10),
            panel_ratios=panel_ratios,
            tight_layout=True,
            returnfig=True,
            warn_too_much_data=9999,
        )
        
        # Add support/resistance lines
        if show_sr and len(data) > 20:
            supports, resistances = _find_support_resistance(data)
            ax_main = axes[0]
            for s in supports:
                ax_main.axhline(y=s, color='#00ff88', linewidth=0.7, linestyle=':', alpha=0.6)
            for r in resistances:
                ax_main.axhline(y=r, color='#ff3366', linewidth=0.7, linestyle=':', alpha=0.6)
        
        # Add JARVIS watermark
        fig.text(0.99, 0.01, 'JARVIS AI Trading 🧠',
                fontsize=8, color='#444444', ha='right', va='bottom',
                style='italic', alpha=0.5)
        
        # Save
        fig.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor='#0e1117', edgecolor='none')
        plt.close(fig)
        
        logger.info(f"[CHART-ENGINE] 📊 Chart generated: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"[CHART-ENGINE] Chart generation error: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  NLU — PARSE CHART REQUEST
# ═══════════════════════════════════════════════════════════
def parse_chart_request(text: str) -> Dict[str, Any]:
    """
    Parse natural language chart request.
    
    Examples:
        "RELIANCE chart dikhao" → {symbol: RELIANCE, timeframe: daily}
        "NIFTY 1hr chart with RSI and MACD" → {symbol: NIFTY, timeframe: 1h, indicators: [rsi, macd]}
        "show me BTC weekly chart bollinger" → {symbol: BTC, timeframe: weekly, indicators: [bb]}
    """
    import re
    text_lower = text.lower().strip()
    
    result = {
        "symbol": None,
        "timeframe": "daily",
        "indicators": ["sma", "ema", "rsi", "macd", "volume"],
        "show_sr": True,
        "last_n": 100,
    }
    
    # ── Extract timeframe ──
    tf_patterns = {
        r'\b1\s*min': '1m', r'\b5\s*min': '5m', r'\b15\s*min': '15m',
        r'\b30\s*min': '30m', r'\b1\s*h': '1h', r'\bhourly\b': '1h',
        r'\bdaily\b': 'daily', r'\bweekly\b': 'weekly', r'\bmonthly\b': 'monthly',
        r'\b1\s*hr\b': '1h', r'\b1\s*hour\b': '1h',
        r'\b4\s*h': '1h',  # 4h → use 1h
        r'\bday\b': 'daily', r'\bweek\b': 'weekly',
    }
    for pattern, tf in tf_patterns.items():
        if re.search(pattern, text_lower):
            result["timeframe"] = tf
            break
    
    # ── Extract indicators ──
    user_indicators = []
    indicator_map = {
        'sma': [r'\bsma\b', r'\bsimple moving\b'],
        'ema': [r'\bema\b', r'\bexponential\b'],
        'rsi': [r'\brsi\b'],
        'macd': [r'\bmacd\b'],
        'bb': [r'\bbb\b', r'\bbollinger\b', r'\bband\b'],
        'vwap': [r'\bvwap\b'],
        'volume': [r'\bvolume\b', r'\bvol\b'],
    }
    for ind, patterns in indicator_map.items():
        for p in patterns:
            if re.search(p, text_lower):
                user_indicators.append(ind)
                break
    
    if user_indicators:
        # Always include volume
        if 'volume' not in user_indicators:
            user_indicators.append('volume')
        result["indicators"] = user_indicators
    
    # ── Extract symbol ──
    # Remove common words
    clean = text_lower
    remove_words = [
        'chart', 'dikhao', 'dikha', 'show', 'me', 'ka', 'ki', 'ke', 'with',
        'and', 'bhi', 'please', 'bhai', 'sir', 'jarvis', 'daily', 'weekly',
        'monthly', 'hourly', '1hr', '1h', '5min', '15min', '1min', '30min',
        'rsi', 'macd', 'sma', 'ema', 'bollinger', 'bb', 'vwap', 'volume',
        'technical', 'analysis', 'indicator', 'indicators', 'candle', 'candlestick',
        'graph', 'plot', 'draw', 'generate', 'support', 'resistance',
    ]
    for w in remove_words:
        clean = re.sub(r'\b' + w + r'\b', '', clean)
    
    # Find remaining word that looks like a symbol
    words = [w.strip().upper() for w in clean.split() if w.strip() and len(w.strip()) >= 2]
    
    for word in words:
        if word in NSE_SYMBOL_MAP or len(word) >= 2:
            result["symbol"] = word
            break
    
    # Default to NIFTY if no symbol found
    if not result["symbol"]:
        result["symbol"] = "NIFTY"
    
    return result


# ═══════════════════════════════════════════════════════════
#  QUICK ANALYSIS TEXT (accompanies chart)
# ═══════════════════════════════════════════════════════════
def get_chart_analysis(symbol: str, timeframe: str = "daily") -> str:
    """Get quick technical analysis text to send with chart"""
    data = fetch_chart_data(symbol, timeframe)
    if data is None:
        return f"❌ {symbol} ka data available nahi hai"
    
    # Trim
    if len(data) > 200:
        data = data.tail(200).copy()
    
    close = float(data['Close'].iloc[-1])
    prev_close = float(data['Close'].iloc[-2]) if len(data) > 1 else close
    change = close - prev_close
    change_pct = (change / prev_close) * 100 if prev_close else 0
    high = float(data['High'].iloc[-1])
    low = float(data['Low'].iloc[-1])
    vol = int(data['Volume'].iloc[-1]) if data['Volume'].iloc[-1] else 0
    avg_vol = int(data['Volume'].tail(20).mean()) if len(data) > 20 else vol
    
    # RSI
    rsi = _calc_rsi(data)
    rsi_val = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
    
    # MACD
    macd_line, signal, histogram = _calc_macd(data)
    macd_val = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0
    macd_signal = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else 0
    
    # SMAs
    sma20 = float(_calc_sma(data, 20).iloc[-1]) if len(data) > 20 else close
    sma50 = float(_calc_sma(data, 50).iloc[-1]) if len(data) > 50 else close
    sma200 = float(_calc_sma(data, 200).iloc[-1]) if len(data) > 200 else close
    
    # Bollinger
    bb_upper, bb_mid, bb_lower = _calc_bollinger(data) if len(data) > 20 else (None, None, None)
    
    # S/R
    supports, resistances = _find_support_resistance(data) if len(data) > 20 else ([], [])
    
    # Build analysis
    trend_emoji = "🟢" if change >= 0 else "🔴"
    rsi_status = "🔥 OVERBOUGHT" if rsi_val > 70 else "💚 OVERSOLD" if rsi_val < 30 else "⚪ NEUTRAL"
    macd_status = "🟢 BULLISH" if macd_val > macd_signal else "🔴 BEARISH"
    sma_status = "🟢 ABOVE" if close > sma50 else "🔴 BELOW"
    vol_status = "🔥 HIGH VOLUME" if vol > avg_vol * 1.5 else "📉 LOW VOLUME" if vol < avg_vol * 0.5 else "📊 NORMAL"
    
    # Overall signal
    bull_count = sum([
        1 if change >= 0 else 0,
        1 if rsi_val < 70 and rsi_val > 30 else 0,
        1 if macd_val > macd_signal else 0,
        1 if close > sma20 else 0,
        1 if close > sma50 else 0,
    ])
    overall = "🟢 BULLISH" if bull_count >= 4 else "🔴 BEARISH" if bull_count <= 1 else "🟡 NEUTRAL"
    
    tf_display = timeframe.upper()
    sym_display = symbol.strip().upper()
    
    analysis = (
        f"📊 *{sym_display} — Technical Analysis ({tf_display})*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *Price:* ₹{close:,.2f} {trend_emoji} ({change_pct:+.2f}%)\n"
        f"📈 *High:* ₹{high:,.2f} | 📉 *Low:* ₹{low:,.2f}\n"
        f"📊 *Volume:* {vol:,} ({vol_status})\n\n"
        f"🔬 *INDICATORS:*\n"
        f"┣ RSI(14): {rsi_val:.1f} — {rsi_status}\n"
        f"┣ MACD: {macd_val:.2f} — {macd_status}\n"
        f"┣ SMA(20): ₹{sma20:,.2f} — {'Above ✅' if close > sma20 else 'Below ❌'}\n"
        f"┣ SMA(50): ₹{sma50:,.2f} — {sma_status}\n"
    )
    
    if bb_upper is not None:
        bb_u = float(bb_upper.iloc[-1])
        bb_l = float(bb_lower.iloc[-1])
        bb_pos = "Near Upper 🔴" if close > bb_u * 0.98 else "Near Lower 🟢" if close < bb_l * 1.02 else "Middle ⚪"
        analysis += f"┣ Bollinger: {bb_pos}\n"
    
    analysis += f"┗ Trend: {overall}\n\n"
    
    if supports or resistances:
        analysis += "🎯 *SUPPORT & RESISTANCE:*\n"
        for s in supports:
            analysis += f"  🟢 Support: ₹{s:,.2f}\n"
        for r in resistances:
            analysis += f"  🔴 Resistance: ₹{r:,.2f}\n"
        analysis += "\n"
    
    analysis += f"📊 *OVERALL SIGNAL: {overall}*\n"
    
    return analysis


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════
def handle_chart_command(text: str) -> Tuple[Optional[str], str]:
    """
    Main entry point — parse text, generate chart, return (image_path, analysis_text).
    Returns (None, error_message) on failure.
    """
    parsed = parse_chart_request(text)
    symbol = parsed["symbol"]
    timeframe = parsed["timeframe"]
    indicators = parsed["indicators"]
    
    # Generate chart
    chart_path = generate_chart(
        symbol=symbol,
        timeframe=timeframe,
        indicators=indicators,
        show_sr=parsed["show_sr"],
        last_n=parsed["last_n"]
    )
    
    # Generate analysis text
    analysis = get_chart_analysis(symbol, timeframe)
    
    if chart_path:
        return chart_path, analysis
    else:
        return None, f"❌ *{symbol}* ka chart generate nahi ho paya.\n\n{analysis}"


# ═══════════════════════════════════════════════════════════
#  CLEANUP OLD CHARTS
# ═══════════════════════════════════════════════════════════
def cleanup_old_charts(max_age_hours: int = 2):
    """Delete chart images older than max_age_hours"""
    try:
        now = datetime.now()
        for f in os.listdir(CHART_DIR):
            fpath = os.path.join(CHART_DIR, f)
            if os.path.isfile(fpath):
                age = now - datetime.fromtimestamp(os.path.getmtime(fpath))
                if age.total_seconds() > max_age_hours * 3600:
                    os.remove(fpath)
    except Exception:
        pass


if __name__ == "__main__":
    # Test
    path = generate_chart("RELIANCE", "daily")
    print(f"Chart: {path}")
    print(get_chart_analysis("RELIANCE"))
