"""
CoinDCX Web3 Engine — AI/ML Crypto Buy/Sell Signals 🚀
Full integration with CoinDCX Exchange API
Features: Real-time INR prices, Technical Analysis, ML Predictions,
Order Book Analysis, Multi-TF Signals, Top Gainers/Losers
"""

import os
import time
import json
import hmac
import hashlib
import logging
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache

# ML / Technical
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
COINDCX_API_KEY = os.getenv("COINDCX_API_KEY", "")
COINDCX_SECRET = os.getenv("COINDCX_SECRET", "")

BASE_URL = "https://api.coindcx.com"
PUBLIC_URL = "https://public.coindcx.com"

# Fallback top INR symbols (used when API is down)
TOP_INR_SYMBOLS = [
    "BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "BNB", "SUI",
    "AVAX", "DOT", "LINK", "MATIC", "SHIB", "PEPE", "TON",
    "NEAR", "UNI", "ATOM", "FIL", "ARB", "OP", "INJ", "BONK",
    "FLOKI", "HBAR", "ALGO", "FET", "RENDER", "TRX", "LTC"
]

# ═══════════════════════════════════════════════════════════════
# WEB3 TOKEN CATEGORIES — Auto-tagged for all CoinDCX tokens
# ═══════════════════════════════════════════════════════════════
WEB3_CATEGORIES = {
    "Layer 1": ["BTC", "ETH", "SOL", "ADA", "AVAX", "DOT", "ATOM", "NEAR",
                "SUI", "SEI", "TIA", "INJ", "HBAR", "ALGO", "EGLD", "ICP",
                "TON", "TRX", "ETC", "BCH", "LTC", "XLM", "XRP", "KAVA",
                "MINA", "NEO", "ONE", "CELO", "ROSE", "ZIL", "FTM", "THETA",
                "VET", "STX", "TAO", "BERA", "S", "MOVE", "INIT"],
    "Layer 2": ["ARB", "OP", "POL", "IMX", "STRK", "ZK", "MANTA", "METIS",
                "BOBA", "LRC", "ZRO", "SCROLL", "BLAST", "LINEA", "PLUME",
                "MOVR", "MNT", "CORE"],
    "DeFi": ["UNI", "AAVE", "COMP", "CRV", "SUSHI", "SNX", "DYDX", "LDO",
             "MKR", "YFI", "BNT", "CAKE", "JOE", "RAY", "ORCA", "JUP",
             "GNO", "BAL", "LUNA", "DRIFT", "PYTH", "ENA", "ONDO", "ETHFI",
             "LISTA", "RESOLV", "SYRUP", "HUMA"],
    "Meme": ["DOGE", "SHIB", "PEPE", "BONK", "FLOKI", "WIF", "BRETT",
             "POPCAT", "PNUT", "MOODENG", "TURBO", "BOME", "DOGS", "CAT",
             "MEW", "MYRO", "PONKE", "SLERF", "TOSHI", "FARTCOIN", "TRUMP",
             "MELANIA", "VINE", "SUNDOG", "CHILLGUY", "MEME", "MEMEFI",
             "GOAT", "SPX", "GRIFFAIN", "MIGGLES", "ELIZAOS", "HIPPO",
             "NOT", "HMSTR", "VINU", "HOT", "WIN", "TST", "ANIME", "PUMP",
             "PEIPEI", "VIRTUAL", "WEN"],
    "AI & Data": ["FET", "RENDER", "CGPT", "AI", "AIOZ", "AIXBT", "GRT",
                  "OCEAN", "ARKM", "IO", "TAO", "GRASS", "VIRTUAL", "KAITO",
                  "COOKIE", "ELIZAOS", "GRIFFAIN"],
    "Gaming & NFT": ["AXS", "GALA", "IMX", "ILV", "PIXEL", "BIGTIME",
                     "ALICE", "SLP", "PYR", "MBOX", "SUPER", "PORTAL",
                     "NAKA", "MAVIA", "WOD", "SIDUS", "E4C", "MYRIA",
                     "NXPC"],
    "Infrastructure": ["LINK", "FIL", "AR", "STORJ", "GRT", "ANKR",
                       "RLC", "GLM", "SC", "POWR", "AKT", "PUSH",
                       "HNT", "TFUEL", "BNB", "ENS", "W", "WAXL",
                       "SKL", "CELR", "CTK", "COTI"],
    "Fan Tokens": ["CHZ", "PSG", "BAR", "JUV", "ACM", "CITY", "ASR",
                   "ATM", "LAZIO", "PORTO", "SANTOS", "OG"],
    "Stablecoins": ["USDT", "USDC", "DAI", "PAXG", "XAUT"],
    "Privacy": ["ZEC", "ROSE", "SC"],
    "Exchange Tokens": ["BNB", "CRO", "HTX", "OKB", "FTT", "NEXO"],
}

# Intervals for candle data
INTERVALS = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h",
    "8h": "8h", "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
}

# Cache for market data
_cache = {}
_cache_ttl = {}
_known_tokens = set()  # Track known tokens for new-token detection
_new_token_alerts = []  # Queue of newly discovered tokens

def _get_cache(key, ttl=60):
    """Get cached data if not expired"""
    if key in _cache and time.time() - _cache_ttl.get(key, 0) < ttl:
        return _cache[key]
    return None

def _set_cache(key, data):
    _cache[key] = data
    _cache_ttl[key] = time.time()

def _ist_now() -> str:
    """Current IST time string"""
    try:
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime('%I:%M:%S %p IST, %d %b')
    except:
        return datetime.now().strftime('%H:%M:%S IST')

def get_new_token_alerts() -> List[Dict]:
    """Get and clear new token alert queue"""
    global _new_token_alerts
    alerts = _new_token_alerts.copy()
    _new_token_alerts = []
    return alerts


# ═══════════════════════════════════════════════════════════════
# DYNAMIC WEB3 TOKEN DISCOVERY — ALL CoinDCX Tokens
# ═══════════════════════════════════════════════════════════════

def get_all_web3_tokens() -> List[Dict]:
    """
    Dynamically fetch ALL Web3 tokens available on CoinDCX.
    Returns list of dicts with symbol, name, pair, status, category info.
    Cached for 2 minutes for near real-time data. Detects newly listed tokens.
    """
    global _known_tokens, _new_token_alerts
    cached = _get_cache("all_web3_tokens", 120)  # 2-min cache for real-time
    if cached:
        return cached

    try:
        # Get market details for token names
        r = requests.get(f"{BASE_URL}/exchange/v1/markets_details", timeout=15)
        details = r.json() if r.status_code == 200 else []
    except:
        details = []

    try:
        # Get live tickers for prices
        r2 = requests.get(f"{BASE_URL}/exchange/ticker", timeout=15)
        tickers = r2.json() if r2.status_code == 200 else []
    except:
        tickers = []

    # Build ticker lookup
    ticker_map = {}
    for t in tickers:
        mkt = t.get('market', '')
        ticker_map[mkt] = t

    # Process all INR pairs from details
    tokens = []
    seen_symbols = set()

    for d in details:
        if d.get('base_currency_short_name') != 'INR':
            continue
        if d.get('status') != 'active':
            continue
        sym = d.get('target_currency_short_name', '')
        if not sym or sym in ('INR',) or sym in seen_symbols:
            continue
        # Skip stablecoins from main list
        if sym in ('USDT', 'USDC', 'DAI', 'BUSD', 'TUSD'):
            continue
        seen_symbols.add(sym)

        name = d.get('target_currency_name', sym)
        pair = d.get('pair', f'I-{sym}_INR')
        market = d.get('symbol', f'{sym}INR')

        # Get live data from ticker
        tk = ticker_map.get(market, {})
        price = float(tk.get('last_price', 0))
        change = float(tk.get('change_24_hour', 0))
        volume = float(tk.get('volume', 0))
        high = float(tk.get('high', 0))
        low = float(tk.get('low', 0))

        # Auto-categorize
        categories = []
        for cat, syms in WEB3_CATEGORIES.items():
            if sym in syms:
                categories.append(cat)
        if not categories:
            categories = ["Altcoin"]

        tokens.append({
            'symbol': sym,
            'name': name,
            'pair': pair,
            'market': market,
            'price_inr': price,
            'change_24h': change,
            'volume': volume,
            'high_24h': high,
            'low_24h': low,
            'categories': categories,
            'status': 'active'
        })

    # Also add USDT-only tokens not in INR
    for d in details:
        if d.get('base_currency_short_name') != 'USDT':
            continue
        if d.get('status') != 'active':
            continue
        sym = d.get('target_currency_short_name', '')
        if not sym or sym in seen_symbols or sym in ('USDT', 'USDC', 'DAI', 'INR'):
            continue
        seen_symbols.add(sym)

        name = d.get('target_currency_name', sym)
        pair = d.get('pair', f'B-{sym}_USDT')
        market = d.get('symbol', f'{sym}USDT')

        tk = ticker_map.get(market, {})
        price_usdt = float(tk.get('last_price', 0))
        change = float(tk.get('change_24_hour', 0))
        volume = float(tk.get('volume', 0))

        # Convert USDT price to INR
        usdt_tk = ticker_map.get('USDTINR', {})
        usdt_rate = float(usdt_tk.get('last_price', 85))
        price_inr = price_usdt * usdt_rate

        categories = []
        for cat, syms in WEB3_CATEGORIES.items():
            if sym in syms:
                categories.append(cat)
        if not categories:
            categories = ["Altcoin"]

        tokens.append({
            'symbol': sym,
            'name': name,
            'pair': pair,
            'market': market,
            'price_inr': price_inr,
            'price_usdt': price_usdt,
            'change_24h': change,
            'volume': volume,
            'high_24h': 0,
            'low_24h': 0,
            'categories': categories,
            'status': 'active',
            'usdt_only': True
        })

    tokens.sort(key=lambda x: x.get('volume', 0), reverse=True)
    
    # Detect newly listed tokens
    current_symbols = {t['symbol'] for t in tokens}
    if _known_tokens:  # Only after first load
        new_syms = current_symbols - _known_tokens
        for sym in new_syms:
            token_data = next((t for t in tokens if t['symbol'] == sym), None)
            if token_data:
                _new_token_alerts.append(token_data)
                logger.info(f"[NEW TOKEN] 🆕 Detected new CoinDCX listing: {sym}")
    _known_tokens = current_symbols
    
    _set_cache("all_web3_tokens", tokens)
    return tokens


def get_web3_token_count() -> Dict:
    """Get total count of available Web3 tokens"""
    tokens = get_all_web3_tokens()
    inr_count = sum(1 for t in tokens if not t.get('usdt_only'))
    usdt_count = sum(1 for t in tokens if t.get('usdt_only'))
    categories = {}
    for t in tokens:
        for c in t.get('categories', []):
            categories[c] = categories.get(c, 0) + 1
    return {
        'total': len(tokens),
        'inr_pairs': inr_count,
        'usdt_only': usdt_count,
        'categories': dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
    }


def get_tokens_by_category(category: str) -> List[Dict]:
    """Get all tokens in a specific category"""
    tokens = get_all_web3_tokens()
    cat_lower = category.lower()
    return [t for t in tokens if any(c.lower() == cat_lower for c in t.get('categories', []))]


def search_web3_token(query: str) -> List[Dict]:
    """Search tokens by name or symbol"""
    tokens = get_all_web3_tokens()
    q = query.upper().strip()
    results = []
    # Exact symbol match first
    for t in tokens:
        if t['symbol'] == q:
            results.insert(0, t)
        elif q in t['symbol'] or q.lower() in t.get('name', '').lower():
            results.append(t)
    return results[:20]


def get_all_web3_prices(page: int = 1, per_page: int = 30, sort_by: str = "volume") -> Dict:
    """
    Get paginated list of ALL Web3 token prices.
    sort_by: 'volume', 'change', 'price', 'name'
    """
    tokens = get_all_web3_tokens()

    if sort_by == "change":
        tokens_sorted = sorted(tokens, key=lambda x: x.get('change_24h', 0), reverse=True)
    elif sort_by == "price":
        tokens_sorted = sorted(tokens, key=lambda x: x.get('price_inr', 0), reverse=True)
    elif sort_by == "name":
        tokens_sorted = sorted(tokens, key=lambda x: x.get('symbol', ''))
    else:  # volume
        tokens_sorted = sorted(tokens, key=lambda x: x.get('volume', 0), reverse=True)

    total = len(tokens_sorted)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page

    return {
        'tokens': tokens_sorted[start:end],
        'page': page,
        'total_pages': total_pages,
        'total_tokens': total,
        'sort_by': sort_by
    }


def get_web3_gainers_losers(limit: int = 15) -> Dict:
    """Get top gainers and losers from ALL Web3 tokens"""
    tokens = get_all_web3_tokens()
    # Filter active with volume
    active = [t for t in tokens if t.get('volume', 0) > 0 and t.get('price_inr', 0) > 0]
    by_change = sorted(active, key=lambda x: x.get('change_24h', 0), reverse=True)

    gainers = by_change[:limit]
    losers = by_change[-limit:][::-1]

    return {
        'gainers': gainers,
        'losers': losers,
        'total_tokens': len(active),
        'timestamp': datetime.now().strftime("%H:%M IST")
    }


def scan_all_web3_signals(top_n: int = 15, category: str = None) -> List[Dict]:
    """
    Scan ALL Web3 tokens (or by category) using quick TA analysis.
    Returns best buy/sell signals sorted by signal strength.
    Uses fast mode — RSI + EMA + MACD + Volume only (no ML for speed).
    """
    tokens = get_all_web3_tokens()

    # Filter by category if specified
    if category:
        cat_lower = category.lower()
        tokens = [t for t in tokens if any(c.lower() == cat_lower for c in t.get('categories', []))]

    # Sort by volume, take top tokens for analysis
    active = [t for t in tokens if t.get('volume', 0) > 10000 and t.get('price_inr', 0) > 0]
    active.sort(key=lambda x: x['volume'], reverse=True)
    to_scan = active[:60]  # Scan top 60 by volume

    signals = []
    for token in to_scan:
        sym = token['symbol']
        pair = token['pair']
        try:
            # Quick TA (1h candles)
            df = get_candles(pair, "1h", 100)
            if df.empty or len(df) < 30:
                # Try USDT pair
                alt_pair = f"B-{sym}_USDT"
                df = get_candles(alt_pair, "1h", 100)
                if df.empty or len(df) < 30:
                    continue

            close = df['close']

            # Quick indicators (with NaN safety)
            rsi = compute_rsi(close, 14).iloc[-1]
            ema9 = compute_ema(close, 9).iloc[-1]
            ema21 = compute_ema(close, 21).iloc[-1]
            macd_line, sig_line, hist = compute_macd(close)
            macd_val = macd_line.iloc[-1]
            sig_val = sig_line.iloc[-1]
            vol_sma = df['volume'].rolling(20).mean().iloc[-1]
            vol_ratio = df['volume'].iloc[-1] / (vol_sma + 1e-10)

            # Skip if any indicators are NaN/inf
            if any(np.isnan(v) or np.isinf(v) for v in [rsi, ema9, ema21, macd_val, sig_val]):
                continue

            # Score calculation
            score = 0
            if ema9 > ema21: score += 2
            else: score -= 2
            if rsi < 30: score += 2
            elif rsi > 70: score -= 2
            elif rsi < 45: score += 1
            elif rsi > 55: score -= 1
            if macd_val > sig_val: score += 2
            else: score -= 2
            if vol_ratio > 1.5: score += 1
            if token.get('change_24h', 0) > 3: score += 1
            elif token.get('change_24h', 0) < -3: score -= 1

            if score >= 4:
                signal = "🟢 STRONG BUY"
            elif score >= 2:
                signal = "🟡 BUY"
            elif score <= -4:
                signal = "🔴 STRONG SELL"
            elif score <= -2:
                signal = "🟠 SELL"
            else:
                signal = "⚪ HOLD"

            signals.append({
                'symbol': sym,
                'name': token.get('name', sym),
                'price_inr': token.get('price_inr', 0),
                'change_24h': token.get('change_24h', 0),
                'volume': token.get('volume', 0),
                'categories': token.get('categories', []),
                'rsi': round(rsi, 1),
                'ema_cross': 'BULLISH' if ema9 > ema21 else 'BEARISH',
                'macd_cross': 'BULLISH' if macd_val > sig_val else 'BEARISH',
                'vol_ratio': round(vol_ratio, 1),
                'score': score,
                'signal': signal
            })
        except Exception as e:
            logger.debug(f"Quick scan skip {sym}: {e}")
            continue

    signals.sort(key=lambda x: abs(x['score']), reverse=True)
    return signals[:top_n]


# ═══════════════════════════════════════════════════════════════
# API FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _headers():
    """API headers"""
    h = {"Content-Type": "application/json"}
    if COINDCX_API_KEY:
        h["X-AUTH-APIKEY"] = COINDCX_API_KEY
    return h

def _signed_request(endpoint: str, body: dict = None) -> dict:
    """Make authenticated API request"""
    if not COINDCX_SECRET:
        return {"error": "API Secret not configured"}
    body = body or {}
    body["timestamp"] = int(time.time() * 1000)
    json_body = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(
        COINDCX_SECRET.encode('utf-8'),
        json_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-AUTH-APIKEY": COINDCX_API_KEY,
        "X-AUTH-SIGNATURE": signature
    }
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", data=json_body, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_all_tickers() -> List[Dict]:
    """Get all market tickers"""
    cached = _get_cache("tickers", 30)
    if cached:
        return cached
    try:
        r = requests.get(f"{BASE_URL}/exchange/ticker", headers=_headers(), timeout=10)
        data = r.json()
        _set_cache("tickers", data)
        return data
    except Exception as e:
        logger.error(f"Ticker error: {e}")
        return []

def get_inr_tickers() -> List[Dict]:
    """Get only INR market tickers"""
    all_t = get_all_tickers()
    return [t for t in all_t if t.get("market", "").endswith("INR")]

def get_market_details() -> List[Dict]:
    """Get all market pair details"""
    cached = _get_cache("market_details", 300)
    if cached:
        return cached
    try:
        r = requests.get(f"{BASE_URL}/exchange/v1/markets_details", headers=_headers(), timeout=10)
        data = r.json()
        _set_cache("market_details", data)
        return data
    except Exception as e:
        logger.error(f"Market details error: {e}")
        return []

def get_candles(pair: str, interval: str = "1h", limit: int = 100) -> pd.DataFrame:
    """
    Get OHLCV candle data
    pair format: I-BTC_INR or B-BTC_USDT
    """
    cache_key = f"candles_{pair}_{interval}_{limit}"
    cached = _get_cache(cache_key, 60)
    if cached is not None:
        return cached
    try:
        url = f"{PUBLIC_URL}/market_data/candles?pair={pair}&interval={interval}&limit={limit}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if not data or isinstance(data, dict):
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df = df.sort_values('time').reset_index(drop=True)
        _set_cache(cache_key, df)
        return df
    except Exception as e:
        logger.error(f"Candles error for {pair}: {e}")
        return pd.DataFrame()

def get_orderbook(pair: str) -> Dict:
    """Get order book for a pair"""
    try:
        r = requests.get(f"{PUBLIC_URL}/market_data/orderbook?pair={pair}", timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"Orderbook error: {e}")
        return {}

def get_trade_history(pair: str, limit: int = 50) -> List[Dict]:
    """Get recent trade history"""
    try:
        r = requests.get(f"{PUBLIC_URL}/market_data/trade_history?pair={pair}&limit={limit}", timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"Trade history error: {e}")
        return []

def get_user_balances() -> List[Dict]:
    """Get user wallet balances (needs API secret)"""
    return _signed_request("/exchange/v1/users/balances")


# ═══════════════════════════════════════════════════════════════
# TECHNICAL ANALYSIS
# ═══════════════════════════════════════════════════════════════

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def compute_bollinger(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def compute_stochastic(df: pd.DataFrame, k_period=14, d_period=3):
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
    d = k.rolling(window=d_period).mean()
    return k, d

def compute_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cumulative_tp_vol = (typical_price * df['volume']).cumsum()
    cumulative_vol = df['volume'].cumsum()
    return cumulative_tp_vol / (cumulative_vol + 1e-10)

def compute_obv(df: pd.DataFrame) -> pd.Series:
    obv = [0]
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i-1]:
            obv.append(obv[-1] + df['volume'].iloc[i])
        elif df['close'].iloc[i] < df['close'].iloc[i-1]:
            obv.append(obv[-1] - df['volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def compute_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index"""
    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr = compute_atr(df, 1)
    plus_di = 100 * (plus_dm.rolling(period).mean() / (tr.rolling(period).mean() + 1e-10))
    minus_di = 100 * (minus_dm.rolling(period).mean() / (tr.rolling(period).mean() + 1e-10))
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    return dx.rolling(period).mean()


def full_technical_analysis(df: pd.DataFrame) -> Dict:
    """Run full TA on OHLCV DataFrame, return indicators + signals"""
    if df.empty or len(df) < 30:
        return {"error": "Insufficient data"}
    
    close = df['close']
    result = {}
    
    # Price info
    result['price'] = close.iloc[-1]
    result['price_change_1h'] = ((close.iloc[-1] / close.iloc[-2]) - 1) * 100 if len(df) >= 2 else 0
    result['price_change_24h'] = ((close.iloc[-1] / close.iloc[-24]) - 1) * 100 if len(df) >= 24 else 0
    
    # Moving Averages
    result['ema_9'] = compute_ema(close, 9).iloc[-1]
    result['ema_21'] = compute_ema(close, 21).iloc[-1]
    result['sma_50'] = compute_sma(close, min(50, len(df)-1)).iloc[-1]
    result['sma_200'] = compute_sma(close, min(200, len(df)-1)).iloc[-1] if len(df) > 50 else None
    
    # MA Signals
    result['ema_cross'] = "BULLISH" if result['ema_9'] > result['ema_21'] else "BEARISH"
    result['above_sma50'] = close.iloc[-1] > result['sma_50']
    
    # RSI
    rsi = compute_rsi(close, 14)
    result['rsi'] = rsi.iloc[-1]
    result['rsi_signal'] = "OVERSOLD" if result['rsi'] < 30 else "OVERBOUGHT" if result['rsi'] > 70 else "NEUTRAL"
    
    # MACD
    macd_line, signal_line, histogram = compute_macd(close)
    result['macd'] = macd_line.iloc[-1]
    result['macd_signal'] = signal_line.iloc[-1]
    result['macd_histogram'] = histogram.iloc[-1]
    result['macd_cross'] = "BULLISH" if result['macd'] > result['macd_signal'] else "BEARISH"
    
    # Bollinger Bands
    bb_upper, bb_mid, bb_lower = compute_bollinger(close)
    result['bb_upper'] = bb_upper.iloc[-1]
    result['bb_mid'] = bb_mid.iloc[-1]
    result['bb_lower'] = bb_lower.iloc[-1]
    bb_position = (close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1] + 1e-10)
    result['bb_position'] = bb_position
    result['bb_signal'] = "OVERSOLD" if bb_position < 0.2 else "OVERBOUGHT" if bb_position > 0.8 else "NEUTRAL"
    
    # ATR (Volatility)
    atr = compute_atr(df, 14)
    result['atr'] = atr.iloc[-1]
    result['atr_pct'] = (result['atr'] / close.iloc[-1]) * 100
    
    # Stochastic
    stoch_k, stoch_d = compute_stochastic(df)
    result['stoch_k'] = stoch_k.iloc[-1]
    result['stoch_d'] = stoch_d.iloc[-1]
    result['stoch_signal'] = "OVERSOLD" if result['stoch_k'] < 20 else "OVERBOUGHT" if result['stoch_k'] > 80 else "NEUTRAL"
    
    # VWAP
    result['vwap'] = compute_vwap(df).iloc[-1]
    result['above_vwap'] = close.iloc[-1] > result['vwap']
    
    # OBV trend
    obv = compute_obv(df)
    obv_sma = obv.rolling(10).mean()
    result['obv_trend'] = "BULLISH" if obv.iloc[-1] > obv_sma.iloc[-1] else "BEARISH"
    
    # ADX
    adx = compute_adx(df)
    result['adx'] = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0
    result['trend_strength'] = "STRONG" if result['adx'] > 25 else "WEAK"
    
    # Volume Analysis
    vol_sma = df['volume'].rolling(20).mean()
    result['volume_ratio'] = df['volume'].iloc[-1] / (vol_sma.iloc[-1] + 1e-10)
    result['volume_signal'] = "HIGH" if result['volume_ratio'] > 1.5 else "LOW" if result['volume_ratio'] < 0.5 else "NORMAL"
    
    # Support / Resistance (pivot points)
    h, l, c = df['high'].iloc[-1], df['low'].iloc[-1], close.iloc[-1]
    pivot = (h + l + c) / 3
    result['pivot'] = pivot
    result['support_1'] = 2 * pivot - h
    result['resistance_1'] = 2 * pivot - l
    result['support_2'] = pivot - (h - l)
    result['resistance_2'] = pivot + (h - l)
    
    return result


# ═══════════════════════════════════════════════════════════════
# ORDER BOOK ANALYSIS
# ═══════════════════════════════════════════════════════════════

def analyze_orderbook(pair: str) -> Dict:
    """Analyze order book for buy/sell pressure"""
    ob = get_orderbook(pair)
    if not ob or 'asks' not in ob or 'bids' not in ob:
        return {"error": "No orderbook data"}
    
    asks = ob.get('asks', {})
    bids = ob.get('bids', {})
    
    total_ask_vol = sum(float(v) for v in asks.values()) if asks else 0
    total_bid_vol = sum(float(v) for v in bids.values()) if bids else 0
    
    # Buy/Sell pressure ratio
    total = total_ask_vol + total_bid_vol
    buy_pressure = (total_bid_vol / total * 100) if total > 0 else 50
    sell_pressure = (total_ask_vol / total * 100) if total > 0 else 50
    
    # Bid-Ask spread
    if asks and bids:
        best_ask = min(float(k) for k in asks.keys())
        best_bid = max(float(k) for k in bids.keys())
        spread = ((best_ask - best_bid) / best_bid) * 100
    else:
        best_ask = best_bid = spread = 0
    
    # Wall detection (large orders)
    bid_walls = []
    ask_walls = []
    if bids:
        avg_bid = total_bid_vol / len(bids)
        bid_walls = [(float(p), float(v)) for p, v in bids.items() if float(v) > avg_bid * 3]
    if asks:
        avg_ask = total_ask_vol / len(asks)
        ask_walls = [(float(p), float(v)) for p, v in asks.items() if float(v) > avg_ask * 3]
    
    signal = "🟢 BULLISH" if buy_pressure > 60 else "🔴 BEARISH" if sell_pressure > 60 else "🟡 NEUTRAL"
    
    return {
        "buy_pressure": round(buy_pressure, 1),
        "sell_pressure": round(sell_pressure, 1),
        "spread_pct": round(spread, 4),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "bid_walls": len(bid_walls),
        "ask_walls": len(ask_walls),
        "signal": signal,
        "total_bid_vol": total_bid_vol,
        "total_ask_vol": total_ask_vol
    }


# ═══════════════════════════════════════════════════════════════
# ML PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════════

def _prepare_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare feature matrix for ML model"""
    if df.empty or len(df) < 50:
        return pd.DataFrame()
    
    features = pd.DataFrame(index=df.index)
    close = df['close']
    
    # Price-based
    features['returns_1'] = close.pct_change(1)
    features['returns_3'] = close.pct_change(3)
    features['returns_5'] = close.pct_change(5)
    features['returns_10'] = close.pct_change(10)
    
    # Volatility
    features['volatility_5'] = close.pct_change().rolling(5).std()
    features['volatility_10'] = close.pct_change().rolling(10).std()
    features['volatility_20'] = close.pct_change().rolling(20).std()
    
    # RSI
    features['rsi_14'] = compute_rsi(close, 14)
    features['rsi_7'] = compute_rsi(close, 7)
    
    # MACD
    macd_line, signal_line, histogram = compute_macd(close)
    features['macd'] = macd_line
    features['macd_signal'] = signal_line
    features['macd_histogram'] = histogram
    
    # Bollinger
    bb_upper, bb_mid, bb_lower = compute_bollinger(close)
    features['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower + 1e-10)
    features['bb_width'] = (bb_upper - bb_lower) / (bb_mid + 1e-10)
    
    # Moving averages
    features['ema_9_ratio'] = close / compute_ema(close, 9)
    features['ema_21_ratio'] = close / compute_ema(close, 21)
    features['sma_50_ratio'] = close / compute_sma(close, min(50, len(df)-1))
    
    # Stochastic
    k, d = compute_stochastic(df)
    features['stoch_k'] = k
    features['stoch_d'] = d
    
    # Volume
    features['volume_ratio'] = df['volume'] / (df['volume'].rolling(20).mean() + 1e-10)
    features['volume_change'] = df['volume'].pct_change()
    
    # OBV
    obv = compute_obv(df)
    features['obv_change'] = obv.pct_change(5)
    
    # ATR
    features['atr_pct'] = compute_atr(df) / (close + 1e-10) * 100
    
    # Candle patterns
    features['body_ratio'] = abs(close - df['open']) / (df['high'] - df['low'] + 1e-10)
    features['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / (df['high'] - df['low'] + 1e-10)
    features['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / (df['high'] - df['low'] + 1e-10)
    
    # ADX
    features['adx'] = compute_adx(df)
    
    # Clean infinity and NaN values (prevents sklearn crashes)
    features = features.replace([np.inf, -np.inf], np.nan)
    return features.dropna()


def ml_predict_signal(symbol: str, pair: str = None, interval: str = "1h") -> Dict:
    """
    ML-based price prediction and buy/sell signal
    Uses ensemble of RandomForest + GradientBoosting
    """
    if not ML_AVAILABLE:
        return {"error": "ML libraries not available"}
    
    if not pair:
        pair = f"I-{symbol}_INR"
    
    # Get extended candle data for training
    df = get_candles(pair, interval, limit=500)
    if df.empty or len(df) < 100:
        # Try USDT pair
        df = get_candles(f"B-{symbol}_USDT", interval, limit=500)
        if df.empty or len(df) < 100:
            return {"error": f"Insufficient data for {symbol}"}
    
    # Prepare features
    features_df = _prepare_ml_features(df)
    if features_df.empty or len(features_df) < 60:
        return {"error": "Insufficient features"}
    
    # Create target: 1 if price goes up in next N periods, 0 otherwise
    future_returns = df['close'].pct_change(3).shift(-3)
    aligned_idx = features_df.index.intersection(future_returns.dropna().index)
    
    X = features_df.loc[aligned_idx]
    y = (future_returns.loc[aligned_idx] > 0).astype(int)
    
    if len(X) < 60:
        return {"error": "Insufficient training data"}
    
    # Train/test split
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    # Scale features — with safety for remaining NaN/inf
    scaler = StandardScaler()
    try:
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
    except Exception as e:
        return {"error": f"Feature scaling failed: {str(e)[:60]}"}
    
    # Ensemble models
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=80, max_depth=5, random_state=42)
    
    rf.fit(X_train_scaled, y_train)
    gb.fit(X_train_scaled, y_train)
    
    # Test accuracy
    rf_acc = rf.score(X_test_scaled, y_test)
    gb_acc = gb.score(X_test_scaled, y_test)
    
    # Predict current — clean infinity
    current_features = features_df.iloc[-1:].values
    current_features = np.nan_to_num(current_features, nan=0.0, posinf=0.0, neginf=0.0)
    current_scaled = scaler.transform(current_features)
    
    rf_prob = rf.predict_proba(current_scaled)[0]
    gb_prob = gb.predict_proba(current_scaled)[0]
    
    # Ensemble average
    buy_prob = (rf_prob[1] * 0.5 + gb_prob[1] * 0.5) * 100
    sell_prob = (rf_prob[0] * 0.5 + gb_prob[0] * 0.5) * 100
    
    # Feature importance
    feature_names = features_df.columns.tolist()
    rf_importance = dict(zip(feature_names, rf.feature_importances_))
    top_features = sorted(rf_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Signal determination
    if buy_prob > 65:
        signal = "🟢 STRONG BUY"
        action = "BUY"
    elif buy_prob > 55:
        signal = "🟡 MILD BUY"
        action = "BUY"
    elif sell_prob > 65:
        signal = "🔴 STRONG SELL"
        action = "SELL"
    elif sell_prob > 55:
        signal = "🟠 MILD SELL"
        action = "SELL"
    else:
        signal = "⚪ HOLD"
        action = "HOLD"
    
    return {
        "symbol": symbol,
        "signal": signal,
        "action": action,
        "buy_probability": round(buy_prob, 1),
        "sell_probability": round(sell_prob, 1),
        "rf_accuracy": round(rf_acc * 100, 1),
        "gb_accuracy": round(gb_acc * 100, 1),
        "ensemble_accuracy": round((rf_acc + gb_acc) / 2 * 100, 1),
        "top_features": top_features,
        "interval": interval,
        "data_points": len(df)
    }


# ═══════════════════════════════════════════════════════════════
# COMPOSITE SIGNAL ENGINE
# ═══════════════════════════════════════════════════════════════

def get_composite_signal(symbol: str) -> Dict:
    """
    Master signal combining TA + ML + Order Book for any coin
    Returns comprehensive buy/sell analysis
    """
    pair_inr = f"I-{symbol}_INR"
    pair_usdt = f"B-{symbol}_USDT"
    
    result = {
        "symbol": symbol,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        "errors": []
    }
    
    # 1. Get ticker data
    tickers = get_all_tickers()
    inr_ticker = next((t for t in tickers if t['market'] == f"{symbol}INR"), None)
    usdt_ticker = next((t for t in tickers if t['market'] == f"{symbol}USDT"), None)
    
    if inr_ticker:
        result['price_inr'] = float(inr_ticker['last_price'])
        result['change_24h'] = float(inr_ticker.get('change_24_hour', 0))
        result['volume_inr'] = float(inr_ticker.get('volume', 0))
        result['bid'] = float(inr_ticker.get('bid', 0))
        result['ask'] = float(inr_ticker.get('ask', 0))
        result['high_24h'] = float(inr_ticker.get('high', 0))
        result['low_24h'] = float(inr_ticker.get('low', 0))
    elif usdt_ticker:
        usdt_rate = 85  # approx USDT to INR
        usdt_inr = next((t for t in tickers if t['market'] == 'USDTINR'), None)
        if usdt_inr:
            usdt_rate = float(usdt_inr['last_price'])
        result['price_inr'] = float(usdt_ticker['last_price']) * usdt_rate
        result['change_24h'] = float(usdt_ticker.get('change_24_hour', 0))
        result['price_usdt'] = float(usdt_ticker['last_price'])
    else:
        result['errors'].append("No ticker data")
    
    # 2. Technical Analysis (1h)
    df_1h = get_candles(pair_inr, "1h", 200)
    if df_1h.empty:
        df_1h = get_candles(pair_usdt, "1h", 200)
    
    if not df_1h.empty and len(df_1h) >= 30:
        result['ta'] = full_technical_analysis(df_1h)
    else:
        result['errors'].append("No TA data")
        result['ta'] = {}
    
    # 3. Multi-timeframe TA
    tf_signals = {}
    for tf_name, tf_int in [("15m", "15m"), ("1h", "1h"), ("4h", "4h"), ("1d", "1d")]:
        df_tf = get_candles(pair_inr, tf_int, 100)
        if df_tf.empty:
            df_tf = get_candles(pair_usdt, tf_int, 100)
        if not df_tf.empty and len(df_tf) >= 30:
            ta = full_technical_analysis(df_tf)
            # Score: bullish indicators = +1, bearish = -1
            score = 0
            if ta.get('ema_cross') == 'BULLISH': score += 1
            else: score -= 1
            if ta.get('rsi_signal') == 'OVERSOLD': score += 1
            elif ta.get('rsi_signal') == 'OVERBOUGHT': score -= 1
            if ta.get('macd_cross') == 'BULLISH': score += 1
            else: score -= 1
            if ta.get('bb_signal') == 'OVERSOLD': score += 1
            elif ta.get('bb_signal') == 'OVERBOUGHT': score -= 1
            if ta.get('stoch_signal') == 'OVERSOLD': score += 1
            elif ta.get('stoch_signal') == 'OVERBOUGHT': score -= 1
            if ta.get('above_vwap'): score += 1
            else: score -= 1
            if ta.get('obv_trend') == 'BULLISH': score += 1
            else: score -= 1
            
            if score >= 4: tf_sig = "🟢 BUY"
            elif score >= 2: tf_sig = "🟡 MILD BUY"
            elif score <= -4: tf_sig = "🔴 SELL"
            elif score <= -2: tf_sig = "🟠 MILD SELL"
            else: tf_sig = "⚪ NEUTRAL"
            
            tf_signals[tf_name] = {"signal": tf_sig, "score": score}
    
    result['multi_tf'] = tf_signals
    
    # 4. Order Book Analysis
    ob = analyze_orderbook(pair_inr)
    if 'error' in ob:
        ob = analyze_orderbook(pair_usdt)
    result['orderbook'] = ob
    
    # 5. ML Prediction
    ml = ml_predict_signal(symbol, pair_inr, "1h")
    if 'error' in ml:
        ml = ml_predict_signal(symbol, pair_usdt, "1h")
    result['ml'] = ml
    
    # 6. MASTER SIGNAL — Weighted combination
    scores = []
    weights = []
    
    # TA score (weight: 30%)
    ta = result.get('ta', {})
    ta_score = 0
    if ta.get('ema_cross') == 'BULLISH': ta_score += 15
    else: ta_score -= 15
    if ta.get('rsi', 50) < 30: ta_score += 10
    elif ta.get('rsi', 50) > 70: ta_score -= 10
    if ta.get('macd_cross') == 'BULLISH': ta_score += 15
    else: ta_score -= 15
    if ta.get('above_vwap'): ta_score += 10
    else: ta_score -= 10
    scores.append(ta_score)
    weights.append(0.30)
    
    # ML score (weight: 35%)
    ml_data = result.get('ml', {})
    ml_score = (ml_data.get('buy_probability', 50) - 50) * 2  # -100 to +100
    scores.append(ml_score)
    weights.append(0.35)
    
    # Order book score (weight: 15%)
    ob_data = result.get('orderbook', {})
    ob_score = (ob_data.get('buy_pressure', 50) - 50) * 2
    scores.append(ob_score)
    weights.append(0.15)
    
    # Multi-TF score (weight: 20%)
    mtf_scores = [v.get('score', 0) for v in tf_signals.values()]
    mtf_avg = np.mean(mtf_scores) * 10 if mtf_scores else 0
    scores.append(mtf_avg)
    weights.append(0.20)
    
    # Weighted master score (-100 to +100)
    master_score = sum(s * w for s, w in zip(scores, weights))
    
    if master_score > 30:
        master_signal = "🟢 STRONG BUY"
        master_action = "BUY"
        confidence = min(95, 60 + master_score * 0.35)
    elif master_score > 10:
        master_signal = "🟡 BUY"
        master_action = "BUY"
        confidence = 50 + master_score * 0.3
    elif master_score < -30:
        master_signal = "🔴 STRONG SELL"
        master_action = "SELL"
        confidence = min(95, 60 + abs(master_score) * 0.35)
    elif master_score < -10:
        master_signal = "🟠 SELL"
        master_action = "SELL"
        confidence = 50 + abs(master_score) * 0.3
    else:
        master_signal = "⚪ HOLD / WAIT"
        master_action = "HOLD"
        confidence = 40 + abs(master_score) * 0.2
    
    result['master_signal'] = master_signal
    result['master_action'] = master_action
    result['master_score'] = round(master_score, 1)
    result['confidence'] = round(min(confidence, 98), 1)
    
    # Risk levels
    atr_pct = ta.get('atr_pct', 2)
    if atr_pct > 5:
        result['risk'] = "🔴 HIGH RISK"
    elif atr_pct > 3:
        result['risk'] = "🟡 MEDIUM RISK"
    else:
        result['risk'] = "🟢 LOW RISK"
    
    # Target & Stop Loss
    if result.get('price_inr'):
        price = result['price_inr']
        if master_action == "BUY":
            result['target_1'] = round(price * (1 + atr_pct/100 * 1.5), 2)
            result['target_2'] = round(price * (1 + atr_pct/100 * 3), 2)
            result['stop_loss'] = round(price * (1 - atr_pct/100 * 1), 2)
        elif master_action == "SELL":
            result['target_1'] = round(price * (1 - atr_pct/100 * 1.5), 2)
            result['target_2'] = round(price * (1 - atr_pct/100 * 3), 2)
            result['stop_loss'] = round(price * (1 + atr_pct/100 * 1), 2)
    
    return result


# ═══════════════════════════════════════════════════════════════
# TOP MOVERS & SCREENER
# ═══════════════════════════════════════════════════════════════

def get_top_gainers_losers(limit: int = 10) -> Dict:
    """Get top gainers and losers on CoinDCX INR"""
    tickers = get_inr_tickers()
    if not tickers:
        return {"error": "No ticker data"}
    
    # Filter out stablecoins and low volume
    filtered = []
    for t in tickers:
        mkt = t.get('market', '')
        if mkt in ('USDTINR', 'USDCINR', 'DAIINR', 'BUSDINR', 'TUSDINR'):
            continue
        try:
            vol = float(t.get('volume', 0))
            change = float(t.get('change_24_hour', 0))
            if vol > 100000:  # Min 1L volume
                filtered.append({
                    'market': mkt,
                    'symbol': mkt.replace('INR', ''),
                    'price': float(t['last_price']),
                    'change_24h': change,
                    'volume': vol,
                    'high': float(t.get('high', 0)),
                    'low': float(t.get('low', 0))
                })
        except:
            continue
    
    filtered.sort(key=lambda x: x['change_24h'], reverse=True)
    
    gainers = filtered[:limit]
    losers = filtered[-limit:][::-1]  # Worst first
    
    return {
        "gainers": gainers,
        "losers": losers,
        "total_inr_pairs": len(filtered),
        "timestamp": datetime.now().strftime("%H:%M IST")
    }


def scan_best_signals(top_n: int = 10) -> List[Dict]:
    """
    Scan top INR coins and find best buy/sell signals
    Returns sorted by signal strength
    """
    tickers = get_inr_tickers()
    # Sort by volume, take top coins
    valid = []
    for t in tickers:
        mkt = t.get('market', '')
        if mkt in ('USDTINR', 'USDCINR', 'DAIINR'):
            continue
        try:
            vol = float(t.get('volume', 0))
            if vol > 500000:
                valid.append((mkt.replace('INR', ''), vol))
        except:
            continue
    
    valid.sort(key=lambda x: x[1], reverse=True)
    symbols_to_scan = [s for s, _ in valid[:20]]  # Top 20 by volume
    
    signals = []
    for sym in symbols_to_scan:
        try:
            sig = get_composite_signal(sym)
            if 'master_score' in sig:
                signals.append({
                    'symbol': sym,
                    'price_inr': sig.get('price_inr', 0),
                    'change_24h': sig.get('change_24h', 0),
                    'master_signal': sig.get('master_signal', '⚪'),
                    'master_score': sig.get('master_score', 0),
                    'confidence': sig.get('confidence', 0),
                    'risk': sig.get('risk', ''),
                    'ml_buy_prob': sig.get('ml', {}).get('buy_probability', 50),
                    'rsi': sig.get('ta', {}).get('rsi', 50)
                })
        except Exception as e:
            logger.error(f"Scan error for {sym}: {e}")
            continue
    
    # Sort by absolute master score (strongest signals first)
    signals.sort(key=lambda x: abs(x['master_score']), reverse=True)
    return signals[:top_n]


# ═══════════════════════════════════════════════════════════════
# FORMAT FUNCTIONS (Telegram Display)
# ═══════════════════════════════════════════════════════════════

def _fmt_inr(value: float) -> str:
    """Format INR price nicely"""
    if value >= 10000000:
        return f"₹{value/10000000:.2f}Cr"
    elif value >= 100000:
        return f"₹{value/100000:.2f}L"
    elif value >= 1000:
        return f"₹{value:,.2f}"
    elif value >= 1:
        return f"₹{value:.2f}"
    elif value >= 0.01:
        return f"₹{value:.4f}"
    else:
        return f"₹{value:.8f}"

def _change_emoji(val: float) -> str:
    if val > 5: return "🚀"
    elif val > 2: return "📈"
    elif val > 0: return "🟢"
    elif val > -2: return "🟡"
    elif val > -5: return "📉"
    else: return "💥"


def _quick_signal(symbol: str, pair: str = None) -> str:
    """Ultra-fast buy/sell signal tag using RSI + EMA crossover only.
    Returns a short emoji string like '🟢BUY' or '🔴SELL' or '⚪HOLD'.
    """
    try:
        if not pair:
            pair = f"I-{symbol}_INR"
        df = get_candles(pair, "1h", 50)
        if df.empty or len(df) < 25:
            df = get_candles(f"B-{symbol}_USDT", "1h", 50)
            if df.empty or len(df) < 25:
                return "⚪HOLD"
        close = df['close']
        rsi = compute_rsi(close, 14).iloc[-1]
        ema9 = compute_ema(close, 9).iloc[-1]
        ema21 = compute_ema(close, 21).iloc[-1]
        if np.isnan(rsi) or np.isnan(ema9) or np.isnan(ema21):
            return "⚪HOLD"
        score = 0
        if ema9 > ema21: score += 1
        else: score -= 1
        if rsi < 30: score += 2
        elif rsi > 70: score -= 2
        elif rsi < 45: score += 1
        elif rsi > 55: score -= 1
        if score >= 2: return "🟢BUY"
        elif score >= 1: return "🟡MILD BUY"
        elif score <= -2: return "🔴SELL"
        elif score <= -1: return "🟠MILD SELL"
        else: return "⚪HOLD"
    except:
        return "⚪HOLD"


def _get_momentum(symbol: str, pair: str = None) -> str:
    """Get real-time price momentum using recent candle data.
    Returns a momentum arrow string like '⬆️+2.3%' or '⬇️-1.1%' or '➡️0.0%'.
    """
    try:
        if not pair:
            pair = f"I-{symbol}_INR"
        df = get_candles(pair, "15m", 10)
        if df.empty or len(df) < 4:
            df = get_candles(f"B-{symbol}_USDT", "15m", 10)
            if df.empty or len(df) < 4:
                return ""
        close = df['close']
        # 1h momentum (last 4 x 15m candles)
        pct = ((close.iloc[-1] - close.iloc[-4]) / close.iloc[-4]) * 100
        if pct > 1: return f"⬆️{pct:+.1f}%"
        elif pct > 0.2: return f"↗️{pct:+.1f}%"
        elif pct < -1: return f"⬇️{pct:+.1f}%"
        elif pct < -0.2: return f"↘️{pct:+.1f}%"
        else: return f"➡️{pct:+.1f}%"
    except:
        return ""


def format_composite_signal(data: Dict, lang: str = "hi") -> str:
    """Format composite signal for Telegram display"""
    sym = data.get('symbol', '?')
    hi = lang == "hi"
    
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"🤖 CoinDCX AI Signal — {sym}")
    lines.append(f"{'═'*30}")
    
    # Master Signal
    ms = data.get('master_signal', '⚪')
    conf = data.get('confidence', 0)
    lines.append(f"\n🎯 {'मास्टर सिग्नल' if hi else 'Master Signal'}: {ms}")
    lines.append(f"📊 {'कॉन्फिडेंस' if hi else 'Confidence'}: {conf}%")
    lines.append(f"⚠️ {'रिस्क' if hi else 'Risk'}: {data.get('risk', 'N/A')}")
    
    # Price
    if data.get('price_inr'):
        price = data['price_inr']
        change = data.get('change_24h', 0)
        emoji = _change_emoji(change)
        lines.append(f"\n💰 {'कीमत' if hi else 'Price'}: {_fmt_inr(price)}")
        lines.append(f"{emoji} 24h: {change:+.2f}%")
        if data.get('high_24h'):
            lines.append(f"📈 High: {_fmt_inr(data['high_24h'])} | 📉 Low: {_fmt_inr(data['low_24h'])}")
    
    # Targets
    if data.get('target_1'):
        lines.append(f"\n🎯 Target 1: {_fmt_inr(data['target_1'])}")
        lines.append(f"🎯 Target 2: {_fmt_inr(data['target_2'])}")
        lines.append(f"🛑 Stop Loss: {_fmt_inr(data['stop_loss'])}")
    
    # Technical Summary
    ta = data.get('ta', {})
    if ta and 'error' not in ta:
        lines.append(f"\n📐 {'टेक्निकल एनालिसिस' if hi else 'Technical Analysis'}:")
        lines.append(f"  RSI: {ta.get('rsi', 0):.1f} ({ta.get('rsi_signal', '')})")
        lines.append(f"  MACD: {ta.get('macd_cross', '')} | EMA: {ta.get('ema_cross', '')}")
        lines.append(f"  BB: {ta.get('bb_signal', '')} | Stoch: {ta.get('stoch_signal', '')}")
        lines.append(f"  VWAP: {'Above ✅' if ta.get('above_vwap') else 'Below ❌'}")
        lines.append(f"  OBV: {ta.get('obv_trend', '')} | ADX: {ta.get('adx', 0):.0f} ({ta.get('trend_strength', '')})")
        lines.append(f"  Vol: {ta.get('volume_signal', '')} ({ta.get('volume_ratio', 0):.1f}x)")
    
    # Multi-TF
    mtf = data.get('multi_tf', {})
    if mtf:
        lines.append(f"\n⏱️ {'मल्टी-टाइमफ्रेम' if hi else 'Multi-Timeframe'}:")
        for tf, info in mtf.items():
            lines.append(f"  {tf}: {info.get('signal', '?')} (score: {info.get('score', 0)})")
    
    # Order Book
    ob = data.get('orderbook', {})
    if ob and 'error' not in ob:
        lines.append(f"\n📖 {'ऑर्डर बुक' if hi else 'Order Book'}: {ob.get('signal', '')}")
        lines.append(f"  Buy: {ob.get('buy_pressure', 0)}% | Sell: {ob.get('sell_pressure', 0)}%")
        lines.append(f"  Spread: {ob.get('spread_pct', 0):.3f}%")
    
    # ML Prediction
    ml = data.get('ml', {})
    if ml and 'error' not in ml:
        lines.append(f"\n🧠 {'ML प्रेडिक्शन' if hi else 'ML Prediction'}: {ml.get('signal', '?')}")
        lines.append(f"  Buy Prob: {ml.get('buy_probability', 0)}% | Sell: {ml.get('sell_probability', 0)}%")
        lines.append(f"  Accuracy: RF={ml.get('rf_accuracy', 0)}% | GB={ml.get('gb_accuracy', 0)}%")
        if ml.get('top_features'):
            top3 = ml['top_features'][:3]
            feats = ", ".join([f"{f[0]}({f[1]:.2f})" for f in top3])
            lines.append(f"  Top Features: {feats}")
    
    lines.append(f"\n🕐 {data.get('timestamp', '')}")
    lines.append(f"⚡ CoinDCX Web3 Engine v1.0")
    
    return "\n".join(lines)


def format_top_movers(data: Dict, lang: str = "hi") -> str:
    """Format top gainers/losers for Telegram"""
    hi = lang == "hi"
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"📊 CoinDCX {'टॉप मूवर्स' if hi else 'Top Movers'} (INR)")
    lines.append(f"{'═'*30}")
    
    # Gainers
    gainers = data.get('gainers', [])
    if gainers:
        lines.append(f"\n🚀 {'टॉप गेनर्स' if hi else 'Top Gainers'}:")
        for i, g in enumerate(gainers[:7], 1):
            lines.append(f"  {i}. {g['symbol']} — {_fmt_inr(g['price'])} ({g['change_24h']:+.1f}%) {_change_emoji(g['change_24h'])}")
    
    # Losers
    losers = data.get('losers', [])
    if losers:
        lines.append(f"\n💥 {'टॉप लूजर्स' if hi else 'Top Losers'}:")
        for i, l in enumerate(losers[:7], 1):
            lines.append(f"  {i}. {l['symbol']} — {_fmt_inr(l['price'])} ({l['change_24h']:+.1f}%) {_change_emoji(l['change_24h'])}")
    
    lines.append(f"\n📈 {'कुल INR पेयर्स' if hi else 'Total INR pairs'}: {data.get('total_inr_pairs', 0)}")
    lines.append(f"🕐 {data.get('timestamp', '')}")
    lines.append(f"⚡ CoinDCX Engine")
    
    return "\n".join(lines)


def format_best_signals(signals: List[Dict], lang: str = "hi") -> str:
    """Format best signals scan for Telegram"""
    hi = lang == "hi"
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"🤖 CoinDCX AI {'बेस्ट सिग्नल्स' if hi else 'Best Signals'}")
    lines.append(f"{'═'*30}")
    
    if not signals:
        lines.append("❌ No signals found")
        return "\n".join(lines)
    
    buy_signals = [s for s in signals if s.get('master_score', 0) > 0]
    sell_signals = [s for s in signals if s.get('master_score', 0) < 0]
    
    if buy_signals:
        lines.append(f"\n🟢 {'खरीदो सिग्नल' if hi else 'BUY Signals'}:")
        for s in buy_signals[:5]:
            lines.append(f"  💎 {s['symbol']} — {_fmt_inr(s.get('price_inr',0))}")
            lines.append(f"     {s.get('master_signal','')} | Conf: {s.get('confidence',0)}% | RSI: {s.get('rsi',0):.0f}")
            lines.append(f"     ML Buy: {s.get('ml_buy_prob',0)}% | {s.get('risk','')}")
    
    if sell_signals:
        lines.append(f"\n🔴 {'बेचो सिग्नल' if hi else 'SELL Signals'}:")
        for s in sell_signals[:5]:
            lines.append(f"  ⚠️ {s['symbol']} — {_fmt_inr(s.get('price_inr',0))}")
            lines.append(f"     {s.get('master_signal','')} | Conf: {s.get('confidence',0)}% | RSI: {s.get('rsi',0):.0f}")
    
    lines.append(f"\n🕐 {datetime.now().strftime('%H:%M IST')}")
    lines.append(f"⚡ CoinDCX AI/ML Engine v1.0")
    
    return "\n".join(lines)


def format_quick_price(symbol: str, lang: str = "hi") -> str:
    """Quick price check for a symbol"""
    tickers = get_all_tickers()
    inr = next((t for t in tickers if t['market'] == f"{symbol.upper()}INR"), None)
    
    if not inr:
        return f"❌ {symbol} CoinDCX पर नहीं मिला" if lang == "hi" else f"❌ {symbol} not found on CoinDCX"
    
    price = float(inr['last_price'])
    change = float(inr.get('change_24_hour', 0))
    vol = float(inr.get('volume', 0))
    high = float(inr.get('high', 0))
    low = float(inr.get('low', 0))
    
    emoji = _change_emoji(change)
    hi = lang == "hi"
    
    lines = [
        f"💰 {symbol.upper()} — CoinDCX",
        f"{'कीमत' if hi else 'Price'}: {_fmt_inr(price)} {emoji}",
        f"24h: {change:+.2f}%",
        f"High: {_fmt_inr(high)} | Low: {_fmt_inr(low)}",
        f"Vol: {_fmt_inr(vol)}",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# QUICK HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def coindcx_signal(symbol: str, lang: str = "hi") -> str:
    """One-call function: Get full AI signal for any coin"""
    try:
        data = get_composite_signal(symbol.upper())
        return format_composite_signal(data, lang)
    except Exception as e:
        logger.error(f"CoinDCX signal error for {symbol}: {e}")
        return f"❌ Error generating signal for {symbol}: {str(e)[:100]}"

def coindcx_top_movers(lang: str = "hi") -> str:
    """One-call function: Get top gainers/losers"""
    try:
        data = get_top_gainers_losers(7)
        return format_top_movers(data, lang)
    except Exception as e:
        return f"❌ Top movers error: {str(e)[:100]}"

def coindcx_best_signals(lang: str = "hi") -> str:
    """One-call function: Scan and find best AI signals"""
    try:
        signals = scan_best_signals(8)
        return format_best_signals(signals, lang)
    except Exception as e:
        return f"❌ Signal scan error: {str(e)[:100]}"

def coindcx_quick_price(symbol: str, lang: str = "hi") -> str:
    """Quick price check"""
    return format_quick_price(symbol.upper(), lang)


# ═══════════════════════════════════════════════════════════════
# ALL WEB3 TOKENS — Format Functions
# ═══════════════════════════════════════════════════════════════

def format_all_web3_tokens(page: int = 1, per_page: int = 25, sort_by: str = "volume", lang: str = "hi") -> str:
    """Format paginated list of ALL Web3 tokens for Telegram"""
    hi = lang == "hi"
    data = get_all_web3_prices(page, per_page, sort_by)
    tokens = data['tokens']
    
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"🌐 CoinDCX {'सभी Web3 टोकन्स' if hi else 'ALL Web3 Tokens'}")
    lines.append(f"{'═'*30}")
    
    sort_labels = {"volume": "📊 Volume", "change": "📈 Change", "price": "💰 Price", "name": "🔤 Name"}
    lines.append(f"Sort: {sort_labels.get(sort_by, sort_by)} | Page {data['page']}/{data['total_pages']}")
    lines.append(f"📊 Total: {data['total_tokens']} tokens\n")
    
    for i, t in enumerate(tokens, (page-1)*per_page + 1):
        sym = t['symbol']
        price = t.get('price_inr', 0)
        change = t.get('change_24h', 0)
        emoji = _change_emoji(change)
        cats = ", ".join(t.get('categories', [])[:2])
        # Quick signal for top 10 tokens only (API rate limit)
        sig = _quick_signal(sym, t.get('pair')) if i <= (page-1)*per_page + 10 else ""
        sig_tag = f" [{sig}]" if sig else ""
        
        price_str = _fmt_inr(price) if price > 0 else "N/A"
        lines.append(f"{i}. {sym} — {price_str} {emoji} ({change:+.1f}%){sig_tag}")
        if cats:
            lines.append(f"   [{cats}]")
    
    lines.append(f"\n📄 Page {data['page']}/{data['total_pages']} | {data['total_tokens']} tokens")
    lines.append(f"💡 {'अगला पेज: /web3 page <n>' if hi else 'Next: /web3 page <n>'}")
    lines.append(f"🕐 LIVE: {_ist_now()}")
    lines.append(f"⚡ CoinDCX Web3 Engine v2.0")
    
    return "\n".join(lines)


def format_web3_category(category: str, lang: str = "hi") -> str:
    """Format tokens by category for Telegram"""
    hi = lang == "hi"
    tokens = get_tokens_by_category(category)
    
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"🏷️ CoinDCX {category} Tokens")
    lines.append(f"{'═'*30}")
    lines.append(f"📊 {len(tokens)} tokens found\n")
    
    # Sort by volume
    tokens.sort(key=lambda x: x.get('volume', 0), reverse=True)
    
    for i, t in enumerate(tokens[:30], 1):
        sym = t['symbol']
        name = t.get('name', sym)
        price = t.get('price_inr', 0)
        change = t.get('change_24h', 0)
        emoji = _change_emoji(change)
        vol = t.get('volume', 0)
        # Quick signal for top 15 tokens only (speed)
        sig = _quick_signal(sym, t.get('pair')) if i <= 15 else ""
        sig_tag = f" [{sig}]" if sig else ""
        # Momentum for top 10
        mom = _get_momentum(sym, t.get('pair')) if i <= 10 else ""
        mom_tag = f" {mom}" if mom else ""
        
        price_str = _fmt_inr(price) if price > 0 else "N/A"
        vol_str = _fmt_inr(vol) if vol > 0 else "—"
        lines.append(f"{i}. {sym} ({name}){sig_tag}{mom_tag}")
        lines.append(f"   {price_str} {emoji} ({change:+.1f}%) | Vol: {vol_str}")
    
    if len(tokens) > 30:
        lines.append(f"\n... +{len(tokens)-30} more tokens")
    
    lines.append(f"\n🕐 LIVE: {_ist_now()}")
    lines.append(f"⚡ CoinDCX Web3 Engine v2.0")
    
    return "\n".join(lines)


def format_web3_scan_signals(signals: List[Dict], category: str = None, lang: str = "hi") -> str:
    """Format Web3 scan signals for Telegram"""
    hi = lang == "hi"
    lines = []
    lines.append(f"{'═'*30}")
    cat_label = f" [{category}]" if category else ""
    lines.append(f"🔍🤖 CoinDCX Web3 AI Scan{cat_label}")
    lines.append(f"{'═'*30}")
    
    if not signals:
        lines.append("❌ No signals found")
        return "\n".join(lines)
    
    buy_sigs = [s for s in signals if s.get('score', 0) > 0]
    sell_sigs = [s for s in signals if s.get('score', 0) < 0]
    neutral = [s for s in signals if s.get('score', 0) == 0]
    
    if buy_sigs:
        lines.append(f"\n🟢 {'खरीदो सिग्नल' if hi else 'BUY Signals'} ({len(buy_sigs)}):")
        for s in buy_sigs[:8]:
            cats = "/".join(s.get('categories', [])[:2])
            lines.append(f"  💎 {s['symbol']} — {_fmt_inr(s.get('price_inr',0))}")
            lines.append(f"     {s['signal']} | RSI:{s['rsi']:.0f} | EMA:{s['ema_cross']}")
            lines.append(f"     MACD:{s['macd_cross']} | Vol:{s['vol_ratio']}x | 24h:{s['change_24h']:+.1f}%")
            if cats:
                lines.append(f"     [{cats}]")
    
    if sell_sigs:
        lines.append(f"\n🔴 {'बेचो सिग्नल' if hi else 'SELL Signals'} ({len(sell_sigs)}):")
        for s in sell_sigs[:8]:
            cats = "/".join(s.get('categories', [])[:2])
            lines.append(f"  ⚠️ {s['symbol']} — {_fmt_inr(s.get('price_inr',0))}")
            lines.append(f"     {s['signal']} | RSI:{s['rsi']:.0f} | EMA:{s['ema_cross']}")
            lines.append(f"     MACD:{s['macd_cross']} | Vol:{s['vol_ratio']}x | 24h:{s['change_24h']:+.1f}%")
            if cats:
                lines.append(f"     [{cats}]")
    
    lines.append(f"\n📊 Scanned {len(signals)} tokens from {len(get_all_web3_tokens())} total")
    lines.append(f"🕐 LIVE: {_ist_now()}")
    lines.append(f"⚡ CoinDCX Web3 AI Scan v2.0")
    
    return "\n".join(lines)


def format_web3_search_results(query: str, lang: str = "hi") -> str:
    """Format token search results for Telegram"""
    hi = lang == "hi"
    results = search_web3_token(query)
    
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"🔎 {'खोज' if hi else 'Search'}: \"{query}\"")
    lines.append(f"{'═'*30}")
    
    if not results:
        lines.append(f"❌ {'कोई टोकन नहीं मिला' if hi else 'No tokens found'}")
        lines.append(f"💡 {'सही symbol लिखें जैसे BTC, SOL, PEPE' if hi else 'Try a valid symbol like BTC, SOL, PEPE'}")
        return "\n".join(lines)
    
    lines.append(f"📊 {len(results)} {'रिजल्ट मिले' if hi else 'results'}\n")
    
    for i, t in enumerate(results[:15], 1):
        sym = t['symbol']
        name = t.get('name', sym)
        price = t.get('price_inr', 0)
        change = t.get('change_24h', 0)
        emoji = _change_emoji(change)
        cats = ", ".join(t.get('categories', [])[:2])
        sig = _quick_signal(sym, t.get('pair')) if i <= 10 else ""
        sig_tag = f" [{sig}]" if sig else ""
        
        price_str = _fmt_inr(price) if price > 0 else "N/A"
        lines.append(f"{i}. {sym} — {name}{sig_tag}")
        lines.append(f"   {price_str} {emoji} ({change:+.1f}%)")
        if cats:
            lines.append(f"   [{cats}]")
    
    lines.append(f"\n💡 Full signal: /cdx <symbol>")
    lines.append(f"🕐 LIVE: {_ist_now()}")
    lines.append(f"⚡ CoinDCX Web3 Engine v2.0")
    
    return "\n".join(lines)


def format_web3_token_count(lang: str = "hi") -> str:
    """Format token count stats for Telegram"""
    hi = lang == "hi"
    stats = get_web3_token_count()
    
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"🌐 CoinDCX Web3 {'टोकन सम्मरी' if hi else 'Token Summary'}")
    lines.append(f"{'═'*30}")
    lines.append(f"\n🪙 {'कुल टोकन' if hi else 'Total Tokens'}: {stats['total']}")
    lines.append(f"💰 INR {'पेयर्स' if hi else 'Pairs'}: {stats['inr_pairs']}")
    lines.append(f"💵 USDT {'ओनली' if hi else 'Only'}: {stats['usdt_only']}")
    lines.append(f"\n🏷️ {'कैटेगरी' if hi else 'Categories'}:")
    
    cat_emojis = {
        "Layer 1": "🔷", "Layer 2": "🔶", "DeFi": "🏦", "Meme": "🐸",
        "AI & Data": "🤖", "Gaming & NFT": "🎮", "Infrastructure": "🔧",
        "Fan Tokens": "⚽", "Stablecoins": "💲", "Privacy": "🔒",
        "Exchange Tokens": "🏛️", "Altcoin": "🪙"
    }
    for cat, count in stats['categories'].items():
        emoji = cat_emojis.get(cat, "📁")
        lines.append(f"  {emoji} {cat}: {count}")
    
    lines.append(f"\n💡 Commands:")
    lines.append(f"  /web3 — All tokens list")
    lines.append(f"  /web3cat <category> — By category")
    lines.append(f"  /web3scan — AI scan all")
    lines.append(f"  /cdx <symbol> — Full signal")
    lines.append(f"  /web3search <query> — Search")
    lines.append(f"\n🕐 LIVE: {_ist_now()}")
    lines.append(f"⚡ CoinDCX Web3 Engine v2.0")
    
    return "\n".join(lines)


def format_web3_gainers_losers(limit: int = 15, lang: str = "hi") -> str:
    """Format ALL Web3 gainers/losers (not just top volume)"""
    hi = lang == "hi"
    data = get_web3_gainers_losers(limit)
    
    lines = []
    lines.append(f"{'═'*30}")
    lines.append(f"🚀💥 CoinDCX Web3 {'टॉप मूवर्स' if hi else 'Top Movers'}")
    lines.append(f"{'═'*30}")
    lines.append(f"📊 {data['total_tokens']} active tokens scanned\n")
    
    gainers = data.get('gainers', [])
    if gainers:
        lines.append(f"🚀 {'टॉप गेनर्स' if hi else 'TOP GAINERS'}:")
        for i, g in enumerate(gainers[:limit], 1):
            cats = "/".join(g.get('categories', [])[:1])
            cat_tag = f" [{cats}]" if cats else ""
            sig = _quick_signal(g['symbol'], g.get('pair')) if i <= 8 else ""
            sig_tag = f" [{sig}]" if sig else ""
            lines.append(f"  {i}. {g['symbol']} — {_fmt_inr(g['price_inr'])} ({g['change_24h']:+.1f}%) {_change_emoji(g['change_24h'])}{sig_tag}{cat_tag}")
    
    losers = data.get('losers', [])
    if losers:
        lines.append(f"\n💥 {'टॉप लूजर्स' if hi else 'TOP LOSERS'}:")
        for i, l in enumerate(losers[:limit], 1):
            cats = "/".join(l.get('categories', [])[:1])
            cat_tag = f" [{cats}]" if cats else ""
            sig = _quick_signal(l['symbol'], l.get('pair')) if i <= 8 else ""
            sig_tag = f" [{sig}]" if sig else ""
            lines.append(f"  {i}. {l['symbol']} — {_fmt_inr(l['price_inr'])} ({l['change_24h']:+.1f}%) {_change_emoji(l['change_24h'])}{sig_tag}{cat_tag}")
    
    lines.append(f"\n🕐 {data.get('timestamp', '')} | LIVE: {_ist_now()}")
    lines.append(f"⚡ CoinDCX Web3 Engine v2.0")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# ONE-CALL HELPER FUNCTIONS (for Telegram bot)
# ═══════════════════════════════════════════════════════════════

def coindcx_all_web3(page: int = 1, sort_by: str = "volume", lang: str = "hi") -> str:
    """One-call: Get all Web3 tokens (paginated)"""
    try:
        return format_all_web3_tokens(page, 25, sort_by, lang)
    except Exception as e:
        return f"❌ Web3 tokens error: {str(e)[:100]}"

def coindcx_web3_category(category: str, lang: str = "hi") -> str:
    """One-call: Get tokens by category"""
    try:
        return format_web3_category(category, lang)
    except Exception as e:
        return f"❌ Category error: {str(e)[:100]}"

def coindcx_web3_scan(category: str = None, lang: str = "hi") -> str:
    """One-call: AI scan all Web3 tokens"""
    try:
        signals = scan_all_web3_signals(15, category)
        return format_web3_scan_signals(signals, category, lang)
    except Exception as e:
        return f"❌ Scan error: {str(e)[:100]}"

def coindcx_web3_search(query: str, lang: str = "hi") -> str:
    """One-call: Search Web3 tokens"""
    try:
        return format_web3_search_results(query, lang)
    except Exception as e:
        return f"❌ Search error: {str(e)[:100]}"

def coindcx_web3_summary(lang: str = "hi") -> str:
    """One-call: Web3 token count summary"""
    try:
        return format_web3_token_count(lang)
    except Exception as e:
        return f"❌ Summary error: {str(e)[:100]}"

def coindcx_web3_movers(lang: str = "hi") -> str:
    """One-call: ALL Web3 gainers/losers"""
    try:
        return format_web3_gainers_losers(15, lang)
    except Exception as e:
        return f"❌ Movers error: {str(e)[:100]}"


# ═══════════════════════════════════════════════════════════════
# 💰 ₹2K INVESTMENT CALCULATOR — Buy/Sell/Target for EVERY token
# ═══════════════════════════════════════════════════════════════

def calculate_investment(symbol: str, invest_amount: float = 2000, token_data: Dict = None) -> Dict:
    """
    Calculate ₹2K (or custom amount) investment for ANY token.
    Returns: quantity, buy price, sell targets, stop loss, potential profit.
    """
    if not token_data:
        tokens = get_all_web3_tokens()
        token_data = next((t for t in tokens if t['symbol'] == symbol.upper()), None)
    
    if not token_data or token_data.get('price_inr', 0) <= 0:
        return {"error": f"{symbol} ka price nahi mila"}
    
    price = token_data['price_inr']
    change_24h = token_data.get('change_24h', 0)
    high = token_data.get('high_24h', 0)
    low = token_data.get('low_24h', 0)
    volume = token_data.get('volume', 0)
    
    # Quantity you can buy
    quantity = invest_amount / price
    
    # Quick TA signal
    sig = _quick_signal(symbol, token_data.get('pair'))
    
    # ATR-based targets (estimate from 24h range)
    if high > 0 and low > 0 and low > 0:
        daily_range = ((high - low) / low) * 100
    else:
        daily_range = abs(change_24h) * 1.5 if change_24h != 0 else 3.0
    daily_range = max(daily_range, 1.5)  # Min 1.5% range
    
    # Risk assessment
    if daily_range > 15:
        risk = "🔴 HIGH RISK"
        risk_multiplier = 1.5
    elif daily_range > 8:
        risk = "🟡 MEDIUM RISK"
        risk_multiplier = 1.2
    elif daily_range > 4:
        risk = "🟢 MODERATE"
        risk_multiplier = 1.0
    else:
        risk = "🟢 LOW RISK"
        risk_multiplier = 0.8
    
    # Buy at current price
    buy_price = price
    
    # Stop Loss (1x daily range below)
    sl_pct = daily_range * 0.8 * risk_multiplier
    stop_loss = price * (1 - sl_pct / 100)
    sl_loss = invest_amount * sl_pct / 100
    
    # Target 1: 1.5x daily range (short-term)
    t1_pct = daily_range * 1.5
    target_1 = price * (1 + t1_pct / 100)
    t1_profit = invest_amount * t1_pct / 100
    
    # Target 2: 3x daily range (swing)
    t2_pct = daily_range * 3
    target_2 = price * (1 + t2_pct / 100)
    t2_profit = invest_amount * t2_pct / 100
    
    # Target 3: 5x daily range (moonshot)
    t3_pct = daily_range * 5
    target_3 = price * (1 + t3_pct / 100)
    t3_profit = invest_amount * t3_pct / 100
    
    # 50x moonshot (for meme coins)
    moonshot_price = price * 50
    moonshot_profit = invest_amount * 49
    
    # Can ₹2K become ₹2L?
    needed_for_2l = ((200000 / invest_amount) - 1) * 100  # % needed
    
    return {
        "symbol": symbol.upper(),
        "name": token_data.get('name', symbol),
        "invest_amount": invest_amount,
        "price_inr": price,
        "quantity": quantity,
        "change_24h": change_24h,
        "volume": volume,
        "daily_range_pct": round(daily_range, 1),
        "risk": risk,
        "signal": sig or "⚪ HOLD",
        "buy_price": round(buy_price, 8),
        "stop_loss": round(stop_loss, 8),
        "sl_pct": round(sl_pct, 1),
        "sl_loss": round(sl_loss, 2),
        "target_1": round(target_1, 8),
        "t1_pct": round(t1_pct, 1),
        "t1_profit": round(t1_profit, 2),
        "target_2": round(target_2, 8),
        "t2_pct": round(t2_pct, 1),
        "t2_profit": round(t2_profit, 2),
        "target_3": round(target_3, 8),
        "t3_pct": round(t3_pct, 1),
        "t3_profit": round(t3_profit, 2),
        "moonshot_50x": round(moonshot_price, 8),
        "moonshot_profit": round(moonshot_profit, 2),
        "pct_needed_for_2l": round(needed_for_2l, 1),
        "categories": token_data.get('categories', []),
    }


def format_investment_report(data: Dict, lang: str = "hi") -> str:
    """Format single token investment report"""
    if "error" in data:
        return f"❌ {data['error']}"
    
    hi = lang == "hi"
    sym = data['symbol']
    emoji = _change_emoji(data['change_24h'])
    
    lines = [
        f"{'═'*28}",
        f"💰 ${sym} — {'₹2K निवेश रिपोर्ट' if hi else '₹2K Investment Report'}",
        f"{'═'*28}",
        f"",
        f"💎 {data['name']} ({sym})",
        f"💰 {'कीमत' if hi else 'Price'}: {_fmt_inr(data['price_inr'])} {emoji} ({data['change_24h']:+.1f}%)",
        f"📊 Signal: {data['signal']}",
        f"⚠️ Risk: {data['risk']}",
        f"📈 Daily Range: {data['daily_range_pct']}%",
        f"",
        f"🛒 {'₹{:,.0f} निवेश करो तो:' if hi else '₹{:,.0f} Investment:'}".format(data['invest_amount']),
        f"  🪙 Quantity: {data['quantity']:.4f} {sym}",
        f"  💰 Buy: {_fmt_inr(data['buy_price'])}",
        f"",
        f"🛑 Stop Loss: {_fmt_inr(data['stop_loss'])} (-{data['sl_pct']}%)",
        f"   💸 Max Loss: ₹{data['sl_loss']:,.0f}",
        f"",
        f"🎯 Target 1: {_fmt_inr(data['target_1'])} (+{data['t1_pct']}%)",
        f"   💰 Profit: ₹{data['t1_profit']:,.0f}",
        f"🎯 Target 2: {_fmt_inr(data['target_2'])} (+{data['t2_pct']}%)",
        f"   💰 Profit: ₹{data['t2_profit']:,.0f}",
        f"🎯 Target 3: {_fmt_inr(data['target_3'])} (+{data['t3_pct']}%)",
        f"   💰 Profit: ₹{data['t3_profit']:,.0f}",
        f"",
        f"🚀 50x Moon: {_fmt_inr(data['moonshot_50x'])}",
        f"   💰 ₹{data['invest_amount']:,.0f} → ₹{data['moonshot_profit']:,.0f}",
        f"📊 ₹2L {'बनाने के लिए' if hi else 'needs'}: +{data['pct_needed_for_2l']:.0f}%",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 🌐 MEGA DUMP — ALL 613 TOKENS WITH AI SIGNALS + ₹2K CALC
# ═══════════════════════════════════════════════════════════════

def dump_all_tokens_pages(sort_by: str = "volume", lang: str = "hi") -> List[str]:
    """
    Generate ALL Web3 token messages as a list of page strings.
    Each page has ~20 tokens with signal + ₹2K mini calc.
    Returns list of message strings for batch sending.
    """
    hi = lang == "hi"
    tokens = get_all_web3_tokens()
    if not tokens:
        return ["❌ Token data load nahi ho paya"]
    
    # Sort
    if sort_by == "change":
        tokens.sort(key=lambda x: x.get('change_24h', 0), reverse=True)
    elif sort_by == "price":
        tokens.sort(key=lambda x: x.get('price_inr', 0), reverse=True)
    elif sort_by == "name":
        tokens.sort(key=lambda x: x.get('symbol', ''))
    else:  # volume
        tokens.sort(key=lambda x: x.get('volume', 0), reverse=True)
    
    total = len(tokens)
    per_page = 20
    pages = []
    
    for page_num in range(0, total, per_page):
        batch = tokens[page_num:page_num + per_page]
        pg = page_num // per_page + 1
        total_pages = (total + per_page - 1) // per_page
        
        lines = []
        if pg == 1:
            lines.append(f"{'═'*28}")
            lines.append(f"🌐 CoinDCX {'सभी' if hi else 'ALL'} {total} Web3 Tokens")
            lines.append(f"{'═'*28}")
            lines.append(f"AI Signal + ₹2K {'निवेश कैलकुलेटर' if hi else 'Investment Calc'}")
            lines.append(f"{'⏱️ LIVE: ' + _ist_now()}")
            lines.append("")
        
        lines.append(f"📄 Page {pg}/{total_pages}")
        lines.append("")
        
        for i, t in enumerate(batch, page_num + 1):
            sym = t['symbol']
            price = t.get('price_inr', 0)
            change = t.get('change_24h', 0)
            vol = t.get('volume', 0)
            cats = t.get('categories', ['Altcoin'])
            emoji = _change_emoji(change)
            
            # Quick signal (fast, no API call for speed)
            sig = ""
            try:
                sig = _quick_signal(sym, t.get('pair'))
            except:
                pass
            sig_tag = f" [{sig}]" if sig else ""
            
            # ₹2K mini calc
            if price > 0:
                qty = 2000 / price
                # Simple target: 1.5x daily move
                daily = max(abs(change) * 1.2, 2.0)
                t1_profit = 2000 * daily * 1.5 / 100
                sl_loss = 2000 * daily * 0.8 / 100
                t1_price = price * (1 + daily * 1.5 / 100)
                sl_price = price * (1 - daily * 0.8 / 100)
                
                lines.append(
                    f"{i}. ${sym} — {_fmt_inr(price)} {emoji} ({change:+.1f}%){sig_tag}\n"
                    f"   📊 Vol: {_fmt_inr(vol)} | [{', '.join(cats[:1])}]\n"
                    f"   ₹2K → {qty:.2f} {sym} | 🎯{_fmt_inr(t1_price)}(+₹{t1_profit:.0f}) | 🛑{_fmt_inr(sl_price)}(-₹{sl_loss:.0f})"
                )
            else:
                lines.append(f"{i}. ${sym} — Price N/A [{', '.join(cats[:1])}]")
        
        lines.append(f"\n— Page {pg}/{total_pages} —")
        pages.append("\n".join(lines))
    
    return pages


def dump_all_tokens_category_pages(lang: str = "hi") -> List[str]:
    """
    Generate ALL tokens organized by CATEGORY with AI signal + ₹2K calc.
    Returns list of message strings.
    """
    hi = lang == "hi"
    tokens = get_all_web3_tokens()
    if not tokens:
        return ["❌ Token data load nahi ho paya"]
    
    # Group by primary category
    cat_tokens = {}
    for t in tokens:
        cats = t.get('categories', ['Altcoin'])
        primary = cats[0] if cats else 'Altcoin'
        if primary not in cat_tokens:
            cat_tokens[primary] = []
        cat_tokens[primary].append(t)
    
    # Sort categories by token count desc
    cat_order = sorted(cat_tokens.keys(), key=lambda c: len(cat_tokens[c]), reverse=True)
    
    pages = []
    header = (
        f"{'═'*28}\n"
        f"🌐 CoinDCX ALL {len(tokens)} Tokens {'कैटेगरी वाइज' if hi else 'by Category'}\n"
        f"{'═'*28}\n"
        f"AI Signal + ₹2K Calc | {_ist_now()}\n"
    )
    pages.append(header)
    
    for cat in cat_order:
        ct = cat_tokens[cat]
        ct.sort(key=lambda x: x.get('volume', 0), reverse=True)
        
        cat_emojis = {
            "Layer 1": "🔷", "Layer 2": "🔶", "DeFi": "🏦", "Meme": "🐸",
            "AI & Data": "🤖", "Gaming & NFT": "🎮", "Infrastructure": "🔧",
            "Fan Tokens": "⚽", "Stablecoins": "💲", "Privacy": "🔒",
            "Exchange Tokens": "🏛️", "Altcoin": "🪙"
        }
        ce = cat_emojis.get(cat, "🪙")
        
        lines = [f"\n{ce} ━━ {cat} ({len(ct)} tokens) ━━ {ce}\n"]
        
        for i, t in enumerate(ct, 1):
            sym = t['symbol']
            price = t.get('price_inr', 0)
            change = t.get('change_24h', 0)
            emoji = _change_emoji(change)
            
            sig = ""
            try:
                sig = _quick_signal(sym, t.get('pair'))
            except:
                pass
            sig_tag = f"[{sig}]" if sig else ""
            
            if price > 0:
                qty = 2000 / price
                daily = max(abs(change) * 1.2, 2.0)
                t1 = price * (1 + daily * 1.5 / 100)
                sl = price * (1 - daily * 0.8 / 100)
                t1p = 2000 * daily * 1.5 / 100
                
                lines.append(
                    f"  {i}. ${sym} {_fmt_inr(price)} {emoji}({change:+.1f}%) {sig_tag}\n"
                    f"     ₹2K→{qty:.2f} | T:{_fmt_inr(t1)}(+₹{t1p:.0f}) SL:{_fmt_inr(sl)}"
                )
            else:
                lines.append(f"  {i}. ${sym} — Price N/A")
        
        # Split large categories into multiple pages
        full_text = "\n".join(lines)
        if len(full_text) > 3500:
            chunks = _split_text(full_text, 3500)
            pages.extend(chunks)
        else:
            pages.append(full_text)
    
    return pages


def _split_text(text: str, max_len: int = 3500) -> List[str]:
    """Split text at newline boundaries"""
    chunks = []
    while len(text) > max_len:
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    if text.strip():
        chunks.append(text)
    return chunks


def coindcx_token_invest(symbol: str, amount: float = 2000, lang: str = "hi") -> str:
    """One-call: ₹2K investment report for any token"""
    try:
        data = calculate_investment(symbol.upper(), amount)
        return format_investment_report(data, lang)
    except Exception as e:
        return f"❌ Investment calc error: {str(e)[:100]}"


def coindcx_all_tokens_dump(sort_by: str = "volume", lang: str = "hi") -> List[str]:
    """One-call: Get ALL token pages for batch sending"""
    try:
        return dump_all_tokens_pages(sort_by, lang)
    except Exception as e:
        return [f"❌ Dump error: {str(e)[:100]}"]


def coindcx_all_tokens_by_category(lang: str = "hi") -> List[str]:
    """One-call: Get ALL tokens by category for batch sending"""
    try:
        return dump_all_tokens_category_pages(lang)
    except Exception as e:
        return [f"❌ Category dump error: {str(e)[:100]}"]


# ═══════════════════════════════════════════════════════════════
# MODULE TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀 CoinDCX Web3 Engine v3.0 Test")
    print("=" * 40)
    
    tokens = get_all_web3_tokens()
    print(f"✅ Total Web3 Tokens: {len(tokens)}")
    print("\n" + coindcx_web3_summary())
    print("\n" + coindcx_token_invest("BTC"))
    
    pages = coindcx_all_tokens_dump()
    print(f"\n✅ All tokens dump: {len(pages)} pages")
    if pages:
        print(pages[0][:500])
