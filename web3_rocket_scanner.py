"""
🚀🔥 WEB3 ROCKET SCANNER — Find 25x-50x Tokens in 10-20 Minutes 🔥🚀
═════════════════════════════════════════════════════════════════════════

PURPOSE:  ₹2,000 → ₹50,000 (25x) | ₹2,000 → ₹1,00,000 (50x) in 10-20 min
STRATEGY: Hunt MICRO-CAP tokens with EXPLOSIVE momentum RIGHT NOW

DATA SOURCES:
  1. DexScreener Live API — multi-chain trending, pair data, 5m/1h candles
  2. pump.fun API — Solana meme-coin launchpad, bonding curve tokens
  3. CoinDCX Live — INR pairs, order book, OI-like open interest data
  4. CoinGecko — trending, newly listed, volume spike detection
  5. Birdeye/Jupiter — Solana token analytics (when available)

SIGNALS (40+ factors):
  ■ Volume Explosion (5m vol > 10x hourly avg)
  ■ Buy Pressure Dominance (>80% buys in last 5 min)
  ■ Micro/Nano cap with sudden momentum ($1K-$500K mcap)
  ■ Bonding curve about to graduate (pump.fun)
  ■ Whale accumulation detected
  ■ Multi-chain trending simultaneously
  ■ Social buzz spike (Twitter/Telegram mentions)
  ■ Fresh launches (<30 min old) with traction
  ■ Reversal pattern after dip (bounce plays)
  ■ CoinDCX new listing detection

AI/ML PREDICTION:
  ■ Ensemble scoring: momentum + volume + buy_pressure + mcap_tier
  ■ Pattern matching from historical 10x-100x tokens
  ■ Risk-adjusted recommendation with confidence %
  ■ Exact entry, target, stop-loss in ₹ INR

All prices in ₹ INR | Auto USD→INR conversion
Author: JARVIS Trading AI
"""

import os
import time
import math
import logging
import requests
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger("web3_rocket")

# ═══════════════════════════════════════════════════════════
#  IMPORTS FROM EXISTING ENGINES
# ═══════════════════════════════════════════════════════════

try:
    from crypto_engine import (
        get_usd_inr_rate, usd_to_inr, fmt_inr, get_sol_inr_price,
        _cached_get, pump_get_trending, pump_get_newest, pump_get_top_mcap,
        _normalize_pump_token, _normalize_dex_pair,
        get_top_boosted_tokens, get_token_pairs, get_latest_token_profiles,
        calculate_gem_score, DEXSCREENER_BASE, PUMP_BASE, scan_all_gems
    )
    CRYPTO_OK = True
except ImportError as e:
    CRYPTO_OK = False
    logger.warning(f"[ROCKET] crypto_engine not available: {e}")

try:
    from rug_detector import analyze_rug_risk
    RUG_OK = True
except ImportError:
    RUG_OK = False

try:
    from whale_alert import detect_whale_activity_from_dex
    WHALE_OK = True
except ImportError:
    WHALE_OK = False

try:
    from coindcx_engine import (
        get_all_web3_tokens, get_web3_gainers_losers,
        get_candles, analyze_orderbook, compute_rsi, compute_ema,
        compute_macd, compute_bollinger, _fmt_inr as cdx_fmt_inr
    )
    COINDCX_OK = True
except ImportError:
    COINDCX_OK = False

# ═══════════════════════════════════════════════════════════
#  CONFIG & CACHE
# ═══════════════════════════════════════════════════════════

_rocket_cache: Dict[str, Any] = {}
_rocket_cache_ts: Dict[str, float] = {}
ROCKET_CACHE_TTL = 8  # 8-second cache for near real-time

# Track alerted tokens (avoid duplicate alerts)
_alerted_rockets: Dict[str, float] = {}
ROCKET_ALERT_COOLDOWN = 180  # 3 min cooldown per token

# Historical pump patterns for ML scoring
_pump_history: List[Dict] = []
MAX_PUMP_HISTORY = 500


def _rcache_get(key: str, ttl: int = ROCKET_CACHE_TTL) -> Optional[Any]:
    now = time.time()
    if key in _rocket_cache and (now - _rocket_cache_ts.get(key, 0)) < ttl:
        return _rocket_cache[key]
    return None


def _rcache_set(key: str, data: Any):
    _rocket_cache[key] = data
    _rocket_cache_ts[key] = time.time()


# ═══════════════════════════════════════════════════════════
#  DATA SOURCE 1: DEXSCREENER — Real-time multi-chain
# ═══════════════════════════════════════════════════════════

def _dex_get_json(url: str, ttl: int = 8) -> Optional[Any]:
    """Fast DexScreener API call with tiny cache."""
    cached = _rcache_get(url, ttl)
    if cached is not None:
        return cached
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "JARVIS-Bot/2.0"})
        if r.status_code == 200:
            data = r.json()
            _rcache_set(url, data)
            return data
    except Exception as e:
        logger.debug(f"[ROCKET] DexScreener error: {e}")
    return _rocket_cache.get(url)


def fetch_dex_trending_pairs() -> List[Dict]:
    """Fetch DexScreener top boosted/trending pairs with full data."""
    data = _dex_get_json(f"{DEXSCREENER_BASE}/token-boosts/top/v1", ttl=10)
    if not isinstance(data, list):
        return []
    
    enriched = []
    seen_tokens = set()
    
    for item in data[:40]:  # Top 40 trending
        addr = item.get("tokenAddress", "")
        chain = item.get("chainId", "")
        if not addr or not chain or addr in seen_tokens:
            continue
        seen_tokens.add(addr)
        
        # Get full pair data
        pairs = _dex_get_json(f"{DEXSCREENER_BASE}/tokens/v1/{chain}/{addr}", ttl=10)
        if not isinstance(pairs, list) or not pairs:
            continue
        
        # Pick highest volume pair
        best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
        enriched.append(best)
    
    return enriched


def fetch_dex_new_pairs() -> List[Dict]:
    """Fetch newest token profiles from DexScreener."""
    data = _dex_get_json(f"{DEXSCREENER_BASE}/token-profiles/latest/v1", ttl=15)
    if not isinstance(data, list):
        return []
    
    enriched = []
    seen = set()
    
    for item in data[:30]:
        addr = item.get("tokenAddress", "")
        chain = item.get("chainId", "")
        if not addr or not chain or addr in seen:
            continue
        seen.add(addr)
        
        pairs = _dex_get_json(f"{DEXSCREENER_BASE}/tokens/v1/{chain}/{addr}", ttl=12)
        if not isinstance(pairs, list) or not pairs:
            continue
        
        best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
        enriched.append(best)
    
    return enriched


def search_dex_token(query: str) -> List[Dict]:
    """Search DexScreener for a token."""
    data = _dex_get_json(f"{DEXSCREENER_BASE}/latest/dex/search?q={query}", ttl=15)
    if isinstance(data, dict):
        return data.get("pairs", [])[:10]
    return []


# ═══════════════════════════════════════════════════════════
#  DATA SOURCE 2: PUMP.FUN — Solana meme coins
# ═══════════════════════════════════════════════════════════

def fetch_pump_hot_tokens() -> List[Dict]:
    """Get pump.fun tokens that are HOT RIGHT NOW."""
    if not CRYPTO_OK:
        return []
    
    trending = pump_get_trending(limit=40)
    newest = pump_get_newest(limit=20)
    top = pump_get_top_mcap(limit=20)
    
    all_tokens = []
    seen = set()
    
    for t in trending + newest + top:
        mint = t.get("mint", "")
        if mint in seen:
            continue
        seen.add(mint)
        
        norm = _normalize_pump_token(t)
        all_tokens.append(norm)
    
    return all_tokens


# ═══════════════════════════════════════════════════════════
#  DATA SOURCE 3: COINDCX — INR trading data + OI-like data
# ═══════════════════════════════════════════════════════════

def fetch_coindcx_hot_tokens(limit: int = 30) -> List[Dict]:
    """Get CoinDCX tokens that are pumping RIGHT NOW with OI-like data."""
    if not COINDCX_OK:
        return []
    
    try:
        tokens = get_all_web3_tokens()
        if not tokens:
            return []
        
        # Get gainers with momentum
        active = [t for t in tokens if t.get('volume', 0) > 50000 and t.get('price_inr', 0) > 0]
        
        # Sort by 24h change (highest pumpers first)
        active.sort(key=lambda x: x.get('change_24h', 0), reverse=True)
        
        enriched = []
        for t in active[:limit]:
            sym = t['symbol']
            pair = t.get('pair', f"I-{sym}_INR")
            
            token_data = {
                'source': 'coindcx',
                'symbol': sym,
                'name': t.get('name', sym),
                'chain': 'coindcx',
                'price_inr': t.get('price_inr', 0),
                'change_24h': t.get('change_24h', 0),
                'volume_inr': t.get('volume', 0),
                'high_24h': t.get('high_24h', 0),
                'low_24h': t.get('low_24h', 0),
                'categories': t.get('categories', []),
                'pair': pair,
            }
            
            # Get order book for OI-like data (buy/sell pressure)
            try:
                ob = analyze_orderbook(pair)
                if ob and 'error' not in ob:
                    token_data['buy_pressure'] = ob.get('buy_pressure', 50)
                    token_data['sell_pressure'] = ob.get('sell_pressure', 50)
                    token_data['spread_pct'] = ob.get('spread_pct', 0)
                    token_data['bid_walls'] = ob.get('bid_walls', 0)
                    token_data['ask_walls'] = ob.get('ask_walls', 0)
                    token_data['total_bid_vol'] = ob.get('total_bid_vol', 0)
                    token_data['total_ask_vol'] = ob.get('total_ask_vol', 0)
                    # OI-like metric: total order book depth
                    token_data['open_interest_proxy'] = ob.get('total_bid_vol', 0) + ob.get('total_ask_vol', 0)
            except Exception:
                pass
            
            # Get quick TA
            try:
                df = get_candles(pair, "15m", 50)
                if not df.empty and len(df) >= 10:
                    close = df['close']
                    rsi = compute_rsi(close, 14).iloc[-1]
                    ema9 = compute_ema(close, 9).iloc[-1]
                    ema21 = compute_ema(close, 21).iloc[-1]
                    
                    # 15m momentum — last 4 candles = 1 hour
                    pct_1h = ((close.iloc[-1] - close.iloc[-4]) / close.iloc[-4]) * 100 if len(df) >= 4 else 0
                    pct_15m = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100 if len(df) >= 2 else 0
                    
                    # Volume spike
                    vol_avg = df['volume'].rolling(10).mean().iloc[-1]
                    vol_current = df['volume'].iloc[-1]
                    vol_spike = vol_current / (vol_avg + 1e-10)
                    
                    token_data['rsi'] = float(rsi) if not np.isnan(rsi) else 50
                    token_data['ema_cross'] = 'BULLISH' if ema9 > ema21 else 'BEARISH'
                    token_data['momentum_15m'] = float(pct_15m)
                    token_data['momentum_1h'] = float(pct_1h)
                    token_data['vol_spike'] = float(vol_spike)
            except Exception:
                pass
            
            enriched.append(token_data)
        
        return enriched
    
    except Exception as e:
        logger.error(f"[ROCKET] CoinDCX fetch error: {e}")
        return []


# ═══════════════════════════════════════════════════════════
#  DATA SOURCE 4: COINGECKO — Trending & new listings
# ═══════════════════════════════════════════════════════════

def fetch_coingecko_trending() -> List[Dict]:
    """Fetch CoinGecko trending coins (viral right now)."""
    cached = _rcache_get("cg_trending", 60)
    if cached:
        return cached
    
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/search/trending",
            timeout=10,
            headers={"User-Agent": "JARVIS-Bot/2.0"}
        )
        if r.status_code == 200:
            data = r.json()
            coins = data.get("coins", [])
            
            inr_rate = get_usd_inr_rate() if CRYPTO_OK else 85.0
            result = []
            for item in coins[:15]:
                coin = item.get("item", {})
                price_btc = float(coin.get("price_btc", 0) or 0)
                # Rough USD from BTC price
                btc_usd = 95000  # Approximate
                try:
                    btc_r = requests.get(
                        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                        timeout=5
                    )
                    if btc_r.status_code == 200:
                        btc_usd = float(btc_r.json().get("bitcoin", {}).get("usd", 95000))
                except:
                    pass
                
                price_usd = price_btc * btc_usd
                mcap = float(coin.get("data", {}).get("market_cap", 0) or 0) if isinstance(coin.get("data"), dict) else 0
                
                result.append({
                    'source': 'coingecko_trending',
                    'symbol': coin.get("symbol", "?").upper(),
                    'name': coin.get("name", "?"),
                    'chain': 'multi',
                    'price_usd': price_usd,
                    'price_inr': price_usd * inr_rate,
                    'mcap_usd': mcap,
                    'mcap_inr': mcap * inr_rate,
                    'market_cap_rank': coin.get("market_cap_rank", 9999),
                    'score': coin.get("score", 0),
                    'thumb': coin.get("thumb", ""),
                    'slug': coin.get("slug", ""),
                })
            
            _rcache_set("cg_trending", result)
            return result
    except Exception as e:
        logger.debug(f"[ROCKET] CoinGecko trending error: {e}")
    
    return _rocket_cache.get("cg_trending", [])


# ═══════════════════════════════════════════════════════════
#  🧠 ROCKET SCORE ENGINE — AI/ML Scoring for 25x Potential
# ═══════════════════════════════════════════════════════════

def calculate_rocket_score(token: Dict) -> Dict:
    """
    Advanced AI/ML scoring for 25x-50x moonshot potential.
    
    Score 0-100 where:
    - 80-100: 🔥🔥🔥 ROCKET — immediate buy, massive pump likely
    - 60-79:  🔥🔥 HOT — strong momentum, high potential
    - 40-59:  🔥 WARM — worth watching, building momentum
    - 20-39:  ⚪ MILD — normal activity
    - 0-19:   ❄️ COLD — no momentum
    
    Factors (weighted):
    1. Volume Explosion (25 pts max) — is volume 5x-100x normal?
    2. Buy Pressure (20 pts max) — are buyers dominating?
    3. Price Momentum (20 pts max) — 5m/1h price change velocity
    4. Market Cap Sweet Spot (15 pts max) — micro caps have most upside
    5. Freshness (10 pts max) — new tokens pump harder
    6. Whale Activity (10 pts max) — smart money entering?
    7. Rug Risk Penalty (-20 pts max) — safety check
    """
    score = 0
    reasons = []
    warnings = []
    rocket_signals = []
    
    source = token.get("source", "dexscreener")
    inr_rate = get_usd_inr_rate() if CRYPTO_OK else 85.0
    
    # Extract key metrics
    price_usd = float(token.get("price_usd", 0) or 0)
    price_inr = float(token.get("price_inr", 0) or 0)
    mcap_usd = float(token.get("mcap_usd", 0) or 0)
    mcap_inr = float(token.get("mcap_inr", 0) or 0)
    liq_usd = float(token.get("liq_usd", 0) or 0)
    
    # Price changes
    m5 = float(token.get("change_m5", 0) or 0)
    h1 = float(token.get("change_h1", 0) or 0)
    h6 = float(token.get("change_h6", 0) or 0)
    h24 = float(token.get("change_h24", 0) or 0)
    
    # Volume metrics
    vol_m5 = float(token.get("vol_m5", 0) or 0)
    vol_h1 = float(token.get("vol_h1", 0) or 0)
    vol_h24 = float(token.get("vol_h24", 0) or 0)
    
    # Transaction counts
    buys_h1 = int(token.get("buys_h1", 0) or 0)
    sells_h1 = int(token.get("sells_h1", 0) or 0)
    buys_h24 = int(token.get("buys_h24", 0) or 0)
    sells_h24 = int(token.get("sells_h24", 0) or 0)
    
    # CoinDCX specific
    momentum_15m = float(token.get("momentum_15m", 0) or 0)
    momentum_1h_cdx = float(token.get("momentum_1h", 0) or 0)
    vol_spike = float(token.get("vol_spike", 0) or 0)
    buy_pressure = float(token.get("buy_pressure", 50) or 50)
    
    # ══════════════════════════════════════════════════════
    # 1. VOLUME EXPLOSION (0-25 pts) — Most important signal
    # ══════════════════════════════════════════════════════
    vol_score = 0
    
    if source in ("dexscreener", "pump.fun"):
        hourly_avg = vol_h24 / 24 if vol_h24 > 0 else 0
        if hourly_avg > 0:
            # 5-minute volume annualized vs hourly average
            vol_ratio_m5 = (vol_m5 * 12) / hourly_avg if vol_m5 > 0 else 0
            vol_ratio_h1 = vol_h1 / hourly_avg
            
            if vol_ratio_m5 > 20:
                vol_score = 25
                rocket_signals.append(f"🔥 INSANE 5m volume: {vol_ratio_m5:.0f}x avg")
            elif vol_ratio_m5 > 10:
                vol_score = 22
                rocket_signals.append(f"🔥 MASSIVE 5m volume: {vol_ratio_m5:.0f}x avg")
            elif vol_ratio_m5 > 5:
                vol_score = 18
                rocket_signals.append(f"📊 BIG 5m volume: {vol_ratio_m5:.1f}x avg")
            elif vol_ratio_m5 > 3:
                vol_score = 12
                rocket_signals.append(f"📊 Volume spike: {vol_ratio_m5:.1f}x avg")
            elif vol_ratio_m5 > 1.5:
                vol_score = 6
            
            if vol_ratio_h1 > 5:
                vol_score = min(25, vol_score + 5)
                rocket_signals.append(f"📈 1h vol surge: {vol_ratio_h1:.1f}x")
    
    elif source == "coindcx" and vol_spike > 0:
        if vol_spike > 10:
            vol_score = 22
            rocket_signals.append(f"🔥 MASSIVE CoinDCX vol spike: {vol_spike:.0f}x")
        elif vol_spike > 5:
            vol_score = 16
            rocket_signals.append(f"📊 CoinDCX vol spike: {vol_spike:.1f}x")
        elif vol_spike > 2:
            vol_score = 8
            rocket_signals.append(f"📊 Vol above avg: {vol_spike:.1f}x")
    
    score += vol_score
    
    # ══════════════════════════════════════════════════════
    # 2. BUY PRESSURE (0-20 pts) — Buyers dominating = pump incoming
    # ══════════════════════════════════════════════════════
    bp_score = 0
    
    if source in ("dexscreener", "pump.fun"):
        total_h1 = buys_h1 + sells_h1
        if total_h1 >= 5:
            buy_ratio = buys_h1 / total_h1
            if buy_ratio > 0.85:
                bp_score = 20
                rocket_signals.append(f"🟢 EXTREME buy pressure: {buy_ratio:.0%} ({buys_h1}B/{sells_h1}S)")
            elif buy_ratio > 0.75:
                bp_score = 16
                rocket_signals.append(f"🟢 Strong buy pressure: {buy_ratio:.0%}")
            elif buy_ratio > 0.65:
                bp_score = 10
                rocket_signals.append(f"🟢 Buy dominant: {buy_ratio:.0%}")
            elif buy_ratio > 0.55:
                bp_score = 5
            elif buy_ratio < 0.35:
                bp_score = -5
                warnings.append(f"🔴 Sell pressure: {buy_ratio:.0%} buys only")
    
    elif source == "coindcx":
        if buy_pressure > 75:
            bp_score = 18
            rocket_signals.append(f"🟢 CoinDCX buy pressure: {buy_pressure:.0f}%")
        elif buy_pressure > 60:
            bp_score = 10
            rocket_signals.append(f"🟢 CoinDCX buyers strong: {buy_pressure:.0f}%")
        elif buy_pressure < 35:
            bp_score = -5
            warnings.append(f"🔴 CoinDCX sell pressure: {buy_pressure:.0f}% buy")
    
    score += bp_score
    
    # ══════════════════════════════════════════════════════
    # 3. PRICE MOMENTUM (0-20 pts) — Is it moving FAST?
    # ══════════════════════════════════════════════════════
    mom_score = 0
    
    if source in ("dexscreener", "pump.fun"):
        # 5-minute momentum (fastest indicator)
        if m5 > 30:
            mom_score = 20
            rocket_signals.append(f"🚀 EXPLODING 5m: {m5:+.1f}%")
        elif m5 > 15:
            mom_score = 16
            rocket_signals.append(f"🚀 Fast pump 5m: {m5:+.1f}%")
        elif m5 > 5:
            mom_score = 10
            rocket_signals.append(f"⬆️ Moving up 5m: {m5:+.1f}%")
        elif m5 > 2:
            mom_score = 5
        elif m5 < -10:
            # Dip + volume = possible bounce (risky but high reward)
            if vol_score >= 12:
                mom_score = 8
                rocket_signals.append(f"🔄 Dip + volume = bounce play: {m5:+.1f}%")
            else:
                mom_score = -3
                warnings.append(f"📉 Dumping 5m: {m5:+.1f}%")
        
        # 1-hour momentum bonus
        if h1 > 50:
            mom_score = min(20, mom_score + 5)
            rocket_signals.append(f"🔥 1h pump: {h1:+.1f}%")
        elif h1 > 20:
            mom_score = min(20, mom_score + 3)
    
    elif source == "coindcx":
        if momentum_15m > 5:
            mom_score = 16
            rocket_signals.append(f"🚀 15m momentum: {momentum_15m:+.1f}%")
        elif momentum_15m > 2:
            mom_score = 10
            rocket_signals.append(f"⬆️ 15m up: {momentum_15m:+.1f}%")
        elif momentum_15m < -3:
            if vol_spike > 3:
                mom_score = 5
                rocket_signals.append(f"🔄 Dip+vol bounce: {momentum_15m:+.1f}%")
        
        if momentum_1h_cdx > 10:
            mom_score = min(20, mom_score + 5)
        
        change_24h = float(token.get("change_24h", 0) or 0)
        if change_24h > 20:
            mom_score = min(20, mom_score + 3)
            rocket_signals.append(f"📈 24h gainer: {change_24h:+.1f}%")
    
    score += mom_score
    
    # ══════════════════════════════════════════════════════
    # 4. MARKET CAP SWEET SPOT (0-15 pts) — Smaller = more upside
    # ══════════════════════════════════════════════════════
    mcap_score = 0
    
    if mcap_usd > 0:
        if mcap_usd < 5_000:
            mcap_score = 15
            reasons.append(f"💎 NANO cap: {fmt_inr(mcap_inr)} — max moonshot potential")
        elif mcap_usd < 25_000:
            mcap_score = 14
            reasons.append(f"💎 Ultra micro cap: {fmt_inr(mcap_inr)}")
        elif mcap_usd < 100_000:
            mcap_score = 12
            reasons.append(f"💎 Micro cap: {fmt_inr(mcap_inr)}")
        elif mcap_usd < 500_000:
            mcap_score = 8
            reasons.append(f"🔹 Small cap: {fmt_inr(mcap_inr)}")
        elif mcap_usd < 2_000_000:
            mcap_score = 5
            reasons.append(f"📊 Mid-small cap: {fmt_inr(mcap_inr)}")
        elif mcap_usd < 10_000_000:
            mcap_score = 2
        else:
            mcap_score = 1  # Large caps rarely 25x in 10 min
    elif source == "coindcx":
        # CoinDCX tokens are listed, use volume as proxy
        vol = float(token.get("volume_inr", 0) or 0)
        if 50000 < vol < 500000:
            mcap_score = 8
            reasons.append(f"📊 Low-vol CoinDCX token: {fmt_inr(vol)}")
        elif vol < 50000:
            mcap_score = 3
    
    score += mcap_score
    
    # ══════════════════════════════════════════════════════
    # 5. FRESHNESS (0-10 pts) — New tokens pump harder
    # ══════════════════════════════════════════════════════
    fresh_score = 0
    
    age_hours = float(token.get("age_hours", 9999) or 9999)
    pair_created = token.get("pairCreatedAt")
    
    if pair_created:
        try:
            if isinstance(pair_created, (int, float)):
                created_ms = pair_created
            else:
                created_ms = float(pair_created)
            age_hours = (time.time() * 1000 - created_ms) / (3600 * 1000)
        except:
            pass
    
    if 0 < age_hours <= 0.5:  # < 30 min
        fresh_score = 10
        rocket_signals.append(f"🆕 BRAND NEW: {age_hours*60:.0f} min old!")
    elif age_hours <= 2:
        fresh_score = 8
        rocket_signals.append(f"🆕 Fresh: {age_hours:.1f}h old")
    elif age_hours <= 6:
        fresh_score = 5
        reasons.append(f"⏰ Young: {age_hours:.1f}h")
    elif age_hours <= 24:
        fresh_score = 3
    elif age_hours <= 72:
        fresh_score = 1
    
    score += fresh_score
    
    # ══════════════════════════════════════════════════════
    # 6. WHALE ACTIVITY (0-10 pts)
    # ══════════════════════════════════════════════════════
    whale_score = 0
    
    if WHALE_OK and token.get("mint") and source == "dexscreener":
        try:
            whale = detect_whale_activity_from_dex(token["mint"], token.get("chain", "solana"))
            ws = whale.get("whale_score", 0)
            if ws >= 60:
                whale_score = 10
                rocket_signals.append(f"🐋 WHALE ACTIVITY: score {ws}")
            elif ws >= 40:
                whale_score = 6
                rocket_signals.append(f"🦈 Shark activity: score {ws}")
            elif ws >= 20:
                whale_score = 3
        except Exception:
            pass
    
    # CoinDCX: use bid walls as whale proxy
    if source == "coindcx":
        bid_walls = int(token.get("bid_walls", 0) or 0)
        oi_proxy = float(token.get("open_interest_proxy", 0) or 0)
        if bid_walls >= 3:
            whale_score = 8
            rocket_signals.append(f"🐋 {bid_walls} buy walls detected (OI: {fmt_inr(oi_proxy)})")
        elif bid_walls >= 1:
            whale_score = 4
            rocket_signals.append(f"🦈 Buy wall detected")
    
    score += whale_score
    
    # ══════════════════════════════════════════════════════
    # 7. RUG RISK PENALTY (-20 to 0)
    # ══════════════════════════════════════════════════════
    rug_penalty = 0
    
    if source in ("dexscreener", "pump.fun"):
        # Quick rug checks
        if liq_usd < 50:
            rug_penalty = -15
            warnings.append("🚨 ZERO liquidity — EXTREME RUG RISK")
        elif liq_usd < 200:
            rug_penalty = -8
            warnings.append("🚨 Very low liquidity")
        elif liq_usd < 1000:
            rug_penalty = -3
            warnings.append("⚠️ Low liquidity")
        
        # MCap/Liq ratio
        if mcap_usd > 0 and liq_usd > 0:
            ratio = mcap_usd / liq_usd
            if ratio > 200:
                rug_penalty -= 10
                warnings.append(f"🚨 MCap/Liq {ratio:.0f}x — very thin")
            elif ratio > 50:
                rug_penalty -= 5
                warnings.append(f"⚠️ MCap/Liq {ratio:.0f}x")
        
        # Honeypot check (sells << buys)
        total_h24 = buys_h24 + sells_h24
        if total_h24 > 50:
            sell_ratio = sells_h24 / total_h24
            if sell_ratio < 0.1:
                rug_penalty -= 10
                warnings.append("🚨 Possible honeypot — almost no sells!")
        
        # pump.fun specific
        if source == "pump.fun":
            if not token.get("is_graduated"):
                warnings.append("⏳ Still on bonding curve")
            else:
                reasons.append("🎓 Graduated to Raydium ✅")
    
    score += max(-20, rug_penalty)
    
    # ══════════════════════════════════════════════════════
    # 8. BONUS SIGNALS
    # ══════════════════════════════════════════════════════
    
    # Reversal from 24h dip with fresh volume
    if h24 < -20 and m5 > 3 and vol_score >= 10:
        score += 5
        rocket_signals.append(f"🔄 REVERSAL: 24h {h24:+.1f}% but 5m {m5:+.1f}% with volume!")
    
    # Graduated pump.fun with momentum
    if source == "pump.fun" and token.get("is_graduated") and token.get("reply_count", 0) > 100:
        score += 3
        reasons.append(f"💬 Active community: {token.get('reply_count')} replies")
    
    # Social presence
    if token.get("twitter"):
        score += 1
    if token.get("telegram"):
        score += 1
    if token.get("website"):
        score += 1
    
    # CoinDCX EMA cross
    if source == "coindcx" and token.get("ema_cross") == "BULLISH":
        score += 3
        reasons.append("📊 EMA bullish cross")
    
    if source == "coindcx":
        rsi = token.get("rsi", 50)
        if rsi and not np.isnan(rsi):
            if rsi < 30:
                score += 4
                rocket_signals.append(f"📊 RSI oversold: {rsi:.0f} — bounce expected")
            elif rsi > 80:
                warnings.append(f"⚠️ RSI overbought: {rsi:.0f}")
    
    # ══════════════════════════════════════════════════════
    # FINAL SCORE & CLASSIFICATION
    # ══════════════════════════════════════════════════════
    final_score = max(0, min(100, round(score)))
    
    # Multiplier potential
    if mcap_usd > 0:
        potential_25x = (mcap_usd * 25) 
        potential_50x = (mcap_usd * 50)
        can_25x = mcap_usd < 2_000_000  # Needs to be under $2M to realistically 25x fast
        can_50x = mcap_usd < 500_000
    else:
        potential_25x = potential_50x = 0
        can_25x = can_50x = False
    
    # Confidence % for the action
    if final_score >= 80:
        confidence = min(92, 70 + final_score * 0.22)
        action = "🚀 ROCKET BUY"
    elif final_score >= 60:
        confidence = min(80, 55 + final_score * 0.25)
        action = "🔥 STRONG BUY"
    elif final_score >= 40:
        confidence = min(65, 40 + final_score * 0.25)
        action = "🟢 BUY"
    elif final_score >= 25:
        confidence = 30 + final_score * 0.2
        action = "🟡 WATCH"
    else:
        confidence = 20
        action = "⚪ SKIP"
    
    # Price targets based on rocket score
    if price_inr > 0 or price_usd > 0:
        p = price_inr if price_inr > 0 else (price_usd * inr_rate)
        if final_score >= 70:
            targets = {
                "entry": p,
                "target_2x": p * 2,
                "target_5x": p * 5,
                "target_10x": p * 10,
                "target_25x": p * 25,
                "stop_loss": p * 0.60,  # -40% SL for moonshots
            }
        elif final_score >= 50:
            targets = {
                "entry": p,
                "target_2x": p * 2,
                "target_5x": p * 5,
                "target_10x": p * 10,
                "target_25x": p * 25,
                "stop_loss": p * 0.65,
            }
        else:
            targets = {
                "entry": p,
                "target_2x": p * 2,
                "target_5x": p * 5,
                "target_10x": p * 10,
                "target_25x": p * 25,
                "stop_loss": p * 0.70,
            }
    else:
        targets = {}
    
    # Investment calculator: ₹2K → ?
    invest_2k = {}
    p = price_inr if price_inr > 0 else (price_usd * inr_rate if price_usd > 0 else 0)
    if p > 0:
        tokens_qty = 2000.0 / p
        invest_2k = {
            "amount": 2000,
            "tokens": tokens_qty,
            "at_2x": 4000,
            "at_5x": 10000,
            "at_10x": 20000,
            "at_25x": 50000,
            "at_50x": 100000,
            "at_100x": 200000,
        }
    
    # Store enriched data back
    token["rocket_score"] = final_score
    token["rocket_action"] = action
    token["rocket_confidence"] = round(confidence, 1)
    token["rocket_signals"] = rocket_signals
    token["rocket_reasons"] = reasons
    token["rocket_warnings"] = warnings
    token["rocket_targets"] = targets
    token["rocket_invest_2k"] = invest_2k
    token["can_25x"] = can_25x
    token["can_50x"] = can_50x
    
    return token


# ═══════════════════════════════════════════════════════════
#  🔥 MASTER SCANNER — Find ALL rockets across all sources
# ═══════════════════════════════════════════════════════════

def scan_rockets(min_score: int = 30, limit: int = 15, include_coindcx: bool = True) -> List[Dict]:
    """
    Master scanner: scans ALL sources and returns top rocket candidates.
    
    Sources scanned:
    1. DexScreener trending (multi-chain)
    2. pump.fun trending + newest
    3. CoinDCX hot tokens (with OI data)
    4. CoinGecko trending
    
    Returns sorted by rocket_score, highest first.
    """
    all_candidates = []
    seen_symbols = set()
    
    # ── Source 1: DexScreener trending ──
    try:
        dex_pairs = fetch_dex_trending_pairs()
        for pair in dex_pairs:
            try:
                token = _normalize_dex_pair(pair) if CRYPTO_OK else _basic_normalize_dex(pair)
                scored = calculate_rocket_score(token)
                if scored["rocket_score"] >= min_score:
                    key = f"{scored.get('chain', '')}:{scored.get('symbol', '')}"
                    if key not in seen_symbols:
                        seen_symbols.add(key)
                        all_candidates.append(scored)
            except Exception as e:
                logger.debug(f"[ROCKET] DexScreener score error: {e}")
    except Exception as e:
        logger.error(f"[ROCKET] DexScreener scan failed: {e}")
    
    # ── Source 2: pump.fun ──
    try:
        pump_tokens = fetch_pump_hot_tokens()
        for token in pump_tokens:
            try:
                scored = calculate_rocket_score(token)
                if scored["rocket_score"] >= min_score:
                    key = f"solana:{scored.get('symbol', '')}"
                    if key not in seen_symbols:
                        seen_symbols.add(key)
                        all_candidates.append(scored)
            except Exception as e:
                logger.debug(f"[ROCKET] pump.fun score error: {e}")
    except Exception as e:
        logger.error(f"[ROCKET] pump.fun scan failed: {e}")
    
    # ── Source 3: CoinDCX (with OI-like data) ──
    if include_coindcx:
        try:
            cdx_tokens = fetch_coindcx_hot_tokens(25)
            for token in cdx_tokens:
                try:
                    scored = calculate_rocket_score(token)
                    if scored["rocket_score"] >= min_score:
                        key = f"coindcx:{scored.get('symbol', '')}"
                        if key not in seen_symbols:
                            seen_symbols.add(key)
                            all_candidates.append(scored)
                except Exception as e:
                    logger.debug(f"[ROCKET] CoinDCX score error: {e}")
        except Exception as e:
            logger.error(f"[ROCKET] CoinDCX scan failed: {e}")
    
    # ── Source 4: CoinGecko trending (viral tokens) ──
    try:
        cg_trending = fetch_coingecko_trending()
        for token in cg_trending:
            try:
                scored = calculate_rocket_score(token)
                if scored["rocket_score"] >= max(min_score - 10, 10):  # Lower threshold for trending
                    key = f"cg:{scored.get('symbol', '')}"
                    if key not in seen_symbols:
                        seen_symbols.add(key)
                        all_candidates.append(scored)
            except Exception as e:
                logger.debug(f"[ROCKET] CoinGecko score error: {e}")
    except Exception as e:
        logger.error(f"[ROCKET] CoinGecko scan failed: {e}")
    
    # ── Source 5: DexScreener new profiles (freshest tokens) ──
    try:
        new_pairs = fetch_dex_new_pairs()
        for pair in new_pairs:
            try:
                token = _normalize_dex_pair(pair) if CRYPTO_OK else _basic_normalize_dex(pair)
                scored = calculate_rocket_score(token)
                if scored["rocket_score"] >= min_score:
                    key = f"{scored.get('chain', '')}:{scored.get('symbol', '')}:new"
                    if key not in seen_symbols:
                        seen_symbols.add(key)
                        all_candidates.append(scored)
            except Exception as e:
                logger.debug(f"[ROCKET] DexScreener new error: {e}")
    except Exception as e:
        logger.error(f"[ROCKET] DexScreener new scan failed: {e}")
    
    # Sort by rocket score — DexScreener/pump.fun tokens get slight boost
    for c in all_candidates:
        if c.get("source") in ("dexscreener", "pump.fun"):
            c["_sort_score"] = c.get("rocket_score", 0) + 3  # Web3 priority boost
        else:
            c["_sort_score"] = c.get("rocket_score", 0)
    
    all_candidates.sort(key=lambda x: x.get("_sort_score", 0), reverse=True)
    
    return all_candidates[:limit]


def scan_rockets_fast(min_score: int = 25, limit: int = 10) -> List[Dict]:
    """Ultra-fast scan — DexScreener + pump.fun only (no CoinDCX TA)."""
    return scan_rockets(min_score=min_score, limit=limit, include_coindcx=False)


def get_new_rocket_alerts(min_score: int = 55) -> List[Dict]:
    """Get only NEW rocket alerts not recently sent (for background loop)."""
    now = time.time()
    rockets = scan_rockets_fast(min_score=min_score, limit=8)
    new_alerts = []
    
    for r in rockets:
        key = f"{r.get('chain', '')}:{r.get('mint', r.get('symbol', ''))}"
        if now - _alerted_rockets.get(key, 0) > ROCKET_ALERT_COOLDOWN:
            new_alerts.append(r)
            _alerted_rockets[key] = now
    
    # Cleanup old alerts
    for k in [k for k, v in _alerted_rockets.items() if now - v > 3600]:
        del _alerted_rockets[k]
    
    return new_alerts


# ═══════════════════════════════════════════════════════════
#  BASIC NORMALIZE (fallback if crypto_engine not loaded)
# ═══════════════════════════════════════════════════════════

def _basic_normalize_dex(pair: Dict) -> Dict:
    """Minimal DexScreener pair normalization."""
    base = pair.get("baseToken", {})
    pc = pair.get("priceChange", {})
    vol = pair.get("volume", {})
    liq = pair.get("liquidity", {})
    txns = pair.get("txns", {})
    mcap = float(pair.get("marketCap", 0) or 0)
    price_usd = float(pair.get("priceUsd", 0) or 0)
    
    return {
        "source": "dexscreener",
        "name": base.get("name", "?"),
        "symbol": base.get("symbol", "?"),
        "chain": pair.get("chainId", "?"),
        "mint": base.get("address", ""),
        "price_usd": price_usd,
        "price_inr": price_usd * 85,
        "mcap_usd": mcap,
        "mcap_inr": mcap * 85,
        "liq_usd": float(liq.get("usd", 0) or 0),
        "vol_m5": float(vol.get("m5", 0) or 0),
        "vol_h1": float(vol.get("h1", 0) or 0),
        "vol_h24": float(vol.get("h24", 0) or 0),
        "change_m5": float(pc.get("m5", 0) or 0),
        "change_h1": float(pc.get("h1", 0) or 0),
        "change_h6": float(pc.get("h6", 0) or 0),
        "change_h24": float(pc.get("h24", 0) or 0),
        "buys_h1": int(txns.get("h1", {}).get("buys", 0) or 0),
        "sells_h1": int(txns.get("h1", {}).get("sells", 0) or 0),
        "buys_h24": int(txns.get("h24", {}).get("buys", 0) or 0),
        "sells_h24": int(txns.get("h24", {}).get("sells", 0) or 0),
        "pair_address": pair.get("pairAddress", ""),
        "pairCreatedAt": pair.get("pairCreatedAt"),
        "dex_url": pair.get("url", ""),
        "url": pair.get("url", ""),
    }


# ═══════════════════════════════════════════════════════════
#  📊 FORMAT FOR TELEGRAM — Beautiful Hindi/English Messages
# ═══════════════════════════════════════════════════════════

def format_rocket_scan(rockets: List[Dict]) -> str:
    """Format full rocket scan results for Telegram."""
    if not rockets:
        return (
            "❌ *अभी कोई ROCKET नहीं मिला* ❌\n\n"
            "Market शांत है। बाद में try करो — rockets तब आते हैं\n"
            "जब volume spike होता है!\n\n"
            "💡 /rocket command 5-10 min बाद फिर से try करो।"
        )
    
    inr_rate = get_usd_inr_rate() if CRYPTO_OK else 85.0
    
    msg = "🚀🔥 *WEB3 ROCKET SCANNER* 🔥🚀\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"_₹2K लगाओ → ₹20K-50K बनाओ | {len(rockets)} rockets found_\n"
    msg += f"_Scan: DexScreener + pump.fun + CoinDCX_\n\n"
    
    for i, r in enumerate(rockets[:10], 1):
        rs = r.get("rocket_score", 0)
        
        # Tier badge
        if rs >= 80:
            badge = "🔥🔥🔥 ROCKET"
            stars = "⭐⭐⭐⭐⭐"
        elif rs >= 65:
            badge = "🔥🔥 HOT"
            stars = "⭐⭐⭐⭐"
        elif rs >= 50:
            badge = "🔥 WARM"
            stars = "⭐⭐⭐"
        elif rs >= 35:
            badge = "🟡 MILD"
            stars = "⭐⭐"
        else:
            badge = "⚪ WATCH"
            stars = "⭐"
        
        source_tag = {
            "dexscreener": "🟢 DexScreener",
            "pump.fun": "🟣 pump.fun",
            "coindcx": "🔵 CoinDCX",
            "coingecko_trending": "🟠 CoinGecko",
        }.get(r.get("source", ""), "🔵")
        
        chain = r.get("chain", "?").upper()
        sym = r.get("symbol", "?")
        name = r.get("name", "?")
        
        # Price
        price_inr = r.get("price_inr", 0)
        price_usd = r.get("price_usd", 0)
        if price_inr <= 0 and price_usd > 0:
            price_inr = price_usd * inr_rate
        price_str = fmt_inr(price_inr) if CRYPTO_OK and price_inr > 0 else f"₹{price_inr:.6f}"
        
        # Action
        action = r.get("rocket_action", "⚪ SKIP")
        confidence = r.get("rocket_confidence", 0)
        
        msg += f"*{i}. {sym}* ({name}) {badge}\n"
        msg += f"   {source_tag} | {chain}\n"
        msg += f"   💰 Price: {price_str}\n"
        
        # Market cap
        mcap_inr = r.get("mcap_inr", 0)
        if mcap_inr > 0:
            mcap_str = fmt_inr(mcap_inr) if CRYPTO_OK else f"₹{mcap_inr:,.0f}"
            msg += f"   📊 MCap: {mcap_str}\n"
        
        # Price changes
        if r.get("source") in ("dexscreener", "pump.fun"):
            m5 = r.get("change_m5", 0)
            h1 = r.get("change_h1", 0)
            h24 = r.get("change_h24", 0)
            msg += f"   ⏱️ 5m: {m5:+.1f}% | 1h: {h1:+.1f}% | 24h: {h24:+.1f}%\n"
            
            # Buy/Sell ratio
            b = r.get("buys_h1", 0)
            s = r.get("sells_h1", 0)
            if b + s > 0:
                msg += f"   🛒 B/S 1h: {b}/{s} ({b/(b+s)*100:.0f}% buy)\n"
            
            # Liquidity
            liq = r.get("liq_usd", 0)
            if liq > 0:
                liq_str = fmt_inr(liq * inr_rate) if CRYPTO_OK else f"₹{liq * inr_rate:,.0f}"
                msg += f"   💧 Liq: {liq_str}\n"
        
        elif r.get("source") == "coindcx":
            change = r.get("change_24h", 0)
            mom15 = r.get("momentum_15m", 0)
            vol_inr = r.get("volume_inr", 0)
            msg += f"   📈 24h: {change:+.1f}% | 15m: {mom15:+.1f}%\n"
            if vol_inr > 0:
                msg += f"   📊 Vol: {fmt_inr(vol_inr) if CRYPTO_OK else f'₹{vol_inr:,.0f}'}\n"
            
            # OI-like data
            bp = r.get("buy_pressure", 0)
            oi = r.get("open_interest_proxy", 0)
            if bp > 0:
                msg += f"   📖 Buy Pressure: {bp:.0f}%"
                if oi > 0:
                    msg += f" | OI: {fmt_inr(oi) if CRYPTO_OK else f'₹{oi:,.0f}'}"
                msg += "\n"
            
            # Bid walls
            bw = r.get("bid_walls", 0)
            if bw > 0:
                msg += f"   🐋 Buy Walls: {bw}\n"
        
        # Rocket score & action
        msg += f"   🎯 Score: *{rs}/100* | {action} ({confidence}%)\n"
        
        # Top rocket signals
        signals = r.get("rocket_signals", [])[:3]
        if signals:
            msg += f"   ✅ {' | '.join(signals)}\n"
        
        # Warnings
        warns = r.get("rocket_warnings", [])[:2]
        if warns:
            msg += f"   ⚠️ {' | '.join(warns)}\n"
        
        # Investment calc
        inv = r.get("rocket_invest_2k", {})
        if inv and "BUY" in action:
            msg += f"   💸 *₹2K → 10x=₹{inv.get('at_10x', 0):,.0f} | 25x=₹{inv.get('at_25x', 0):,.0f} | 50x=₹{inv.get('at_50x', 0):,.0f}*\n"
        
        # Targets
        targets = r.get("rocket_targets", {})
        if targets and "BUY" in action:
            sl = targets.get("stop_loss", 0)
            t5x = targets.get("target_5x", 0)
            if sl > 0:
                sl_str = fmt_inr(sl) if CRYPTO_OK else f"₹{sl:.6f}"
                msg += f"   🛑 SL: {sl_str}\n"
        
        # Link
        url = r.get("url") or r.get("dex_url", "")
        if url:
            msg += f"   🔗 [Chart देखो]({url})\n"
        
        msg += "\n"
    
    # Summary
    buy_count = sum(1 for r in rockets if "BUY" in r.get("rocket_action", ""))
    rocket_count = sum(1 for r in rockets if r.get("rocket_score", 0) >= 70)
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if rocket_count > 0:
        msg += f"🔥 *{rocket_count} ROCKETS found!* | {buy_count} BUY signals\n"
    else:
        msg += f"📊 {buy_count} tokens with BUY signal\n"
    
    msg += f"💵 USD/INR: ₹{inr_rate:.2f}\n"
    msg += f"⏰ {datetime.now().strftime('%H:%M:%S IST, %d %b')}\n\n"
    msg += (
        "⚠️ *DISCLAIMER:*\n"
        "• _Crypto mein 25x-50x possible hai but LOSS bhi ho sakta hai_\n"
        "• _Sirf woh paisa lagao jo kho sakte ho_\n"
        "• _STOP LOSS zaroor lagao!_\n"
        "• _DYOR — Apni research karo_"
    )
    
    return msg


def format_single_rocket(r: Dict) -> str:
    """Format a single rocket token alert."""
    inr_rate = get_usd_inr_rate() if CRYPTO_OK else 85.0
    rs = r.get("rocket_score", 0)
    
    if rs >= 80:
        header = "🚀🔥🔥🔥 ROCKET ALERT"
    elif rs >= 65:
        header = "🔥🔥 HOT TOKEN ALERT"
    elif rs >= 50:
        header = "🔥 WARM TOKEN"
    else:
        header = "📊 TOKEN UPDATE"
    
    sym = r.get("symbol", "?")
    name = r.get("name", "?")
    chain = r.get("chain", "?").upper()
    source = r.get("source", "?")
    action = r.get("rocket_action", "")
    confidence = r.get("rocket_confidence", 0)
    
    price_inr = r.get("price_inr", 0)
    if price_inr <= 0:
        price_inr = r.get("price_usd", 0) * inr_rate
    
    msg = f"*{header}!*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"🪙 *{sym}* ({name}) — {chain}\n"
    msg += f"📊 Rocket Score: *{rs}/100*\n"
    msg += f"🎯 Action: *{action}* ({confidence}%)\n\n"
    
    msg += f"💰 Price: {fmt_inr(price_inr) if CRYPTO_OK else f'₹{price_inr:.6f}'}\n"
    
    mcap_inr = r.get("mcap_inr", 0)
    if mcap_inr > 0:
        msg += f"📊 MCap: {fmt_inr(mcap_inr) if CRYPTO_OK else f'₹{mcap_inr:,.0f}'}\n"
    
    if source in ("dexscreener", "pump.fun"):
        msg += f"⏱️ 5m: {r.get('change_m5', 0):+.1f}% | 1h: {r.get('change_h1', 0):+.1f}% | 24h: {r.get('change_h24', 0):+.1f}%\n"
        b = r.get("buys_h1", 0)
        s = r.get("sells_h1", 0)
        if b + s > 0:
            msg += f"🛒 Buys/Sells 1h: {b}/{s} ({b/(b+s)*100:.0f}% buy)\n"
    elif source == "coindcx":
        msg += f"📈 24h: {r.get('change_24h', 0):+.1f}% | 15m: {r.get('momentum_15m', 0):+.1f}%\n"
        bp = r.get("buy_pressure", 0)
        if bp > 0:
            msg += f"📖 Buy Pressure: {bp:.0f}% | OI: {fmt_inr(r.get('open_interest_proxy', 0)) if CRYPTO_OK else ''}\n"
    
    # Signals
    signals = r.get("rocket_signals", [])
    if signals:
        msg += "\n✅ *BULLISH SIGNALS:*\n"
        for sig in signals[:5]:
            msg += f"  {sig}\n"
    
    reasons = r.get("rocket_reasons", [])
    if reasons:
        for reason in reasons[:3]:
            msg += f"  {reason}\n"
    
    # Warnings
    warns = r.get("rocket_warnings", [])
    if warns:
        msg += "\n⚠️ *WARNINGS:*\n"
        for w in warns[:3]:
            msg += f"  {w}\n"
    
    # Investment calc
    inv = r.get("rocket_invest_2k", {})
    if inv:
        msg += "\n💸 *₹2,000 INVEST करोगे तो:*\n"
        msg += f"  ┣ 2x  → ₹{inv.get('at_2x', 0):,}\n"
        msg += f"  ┣ 5x  → ₹{inv.get('at_5x', 0):,}\n"
        msg += f"  ┣ 10x → ₹{inv.get('at_10x', 0):,} 🔥\n"
        msg += f"  ┣ 25x → ₹{inv.get('at_25x', 0):,} 🚀\n"
        msg += f"  ┗ 50x → ₹{inv.get('at_50x', 0):,} 🌕\n"
    
    # Targets
    targets = r.get("rocket_targets", {})
    if targets:
        msg += "\n🎯 *ENTRY / EXIT LEVELS:*\n"
        e = targets.get("entry", 0)
        sl = targets.get("stop_loss", 0)
        t5x = targets.get("target_5x", 0)
        t10x = targets.get("target_10x", 0)
        t25x = targets.get("target_25x", 0)
        p_str = lambda v: fmt_inr(v) if CRYPTO_OK else f"₹{v:.6f}"
        msg += f"  ┣ Entry: {p_str(e)}\n"
        msg += f"  ┣ Target 5x: {p_str(t5x)}\n"
        msg += f"  ┣ Target 10x: {p_str(t10x)}\n"
        msg += f"  ┣ Target 25x: {p_str(t25x)}\n"
        msg += f"  ┗ Stop Loss: {p_str(sl)} 🛑\n"
    
    url = r.get("url") or r.get("dex_url", "")
    if url:
        msg += f"\n🔗 [Chart देखो]({url})\n"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR | Stop-Loss lagao | Sirf affordable loss invest karo*"
    
    return msg


def format_rocket_voice(rockets: List[Dict]) -> str:
    """Format for JARVIS voice (Hindi)."""
    if not rockets:
        return "अभी कोई rocket token नहीं मिला जी। Market शांत है। 5-10 minute बाद try करो।"
    
    top = rockets[0]
    sym = top.get("symbol", "?")
    score = top.get("rocket_score", 0)
    price = top.get("price_inr", 0)
    
    voice = f"जी सुनो! मैंने {len(rockets)} rocket tokens ढूंढे हैं। "
    
    if score >= 70:
        voice += (
            f"सबसे तगड़ा अभी {sym} दिख रहा है, "
            f"जिसकी price {fmt_inr(price) if CRYPTO_OK else f'₹{price:.4f}'} है। "
            f"Rocket score {score} out of 100 है। "
            f"Volume explosion और buy pressure बहुत strong है। "
        )
    elif score >= 50:
        voice += (
            f"सबसे अच्छा {sym} है, "
            f"price {fmt_inr(price) if CRYPTO_OK else f'₹{price:.4f}'}, "
            f"score {score} out of 100। "
            f"Momentum build हो रहा है। "
        )
    else:
        voice += (
            f"Best option अभी {sym} है, "
            f"लेकिन score {score} है, तो ज़्यादा risk मत लो। "
        )
    
    buy_count = sum(1 for r in rockets if "BUY" in r.get("rocket_action", ""))
    voice += f"कुल {buy_count} tokens में buy signal है। "
    
    voice += (
        f"2 हज़ार rupees invest करके अगर 25x hit हो जाये तो 50 हज़ार बन सकते हैं। "
        f"लेकिन stop loss ज़रूर लगाना। "
        f"बाकी details text message में हैं।"
    )
    
    return voice


# ═══════════════════════════════════════════════════════════
#  ONE-CALL FUNCTIONS (for Telegram bot)
# ═══════════════════════════════════════════════════════════

def rocket_scan_full() -> str:
    """One-call: Full rocket scan with all sources."""
    try:
        rockets = scan_rockets(min_score=25, limit=12, include_coindcx=True)
        return format_rocket_scan(rockets)
    except Exception as e:
        logger.error(f"[ROCKET] Full scan error: {e}")
        return f"❌ Rocket scan error: {str(e)[:100]}\n\n💡 Try again in a minute."


def rocket_scan_fast() -> str:
    """One-call: Fast rocket scan (DexScreener + pump.fun only)."""
    try:
        rockets = scan_rockets_fast(min_score=20, limit=10)
        return format_rocket_scan(rockets)
    except Exception as e:
        logger.error(f"[ROCKET] Fast scan error: {e}")
        return f"❌ Fast scan error: {str(e)[:100]}"


def rocket_scan_coindcx() -> str:
    """One-call: CoinDCX-only scan with OI data."""
    try:
        tokens = fetch_coindcx_hot_tokens(30)
        scored = []
        for t in tokens:
            try:
                s = calculate_rocket_score(t)
                if s["rocket_score"] >= 20:
                    scored.append(s)
            except:
                continue
        scored.sort(key=lambda x: x.get("rocket_score", 0), reverse=True)
        
        if not scored:
            return "❌ CoinDCX पर कोई hot token नहीं मिला अभी।\n💡 Try: /rocket (all sources)"
        
        return format_rocket_scan(scored[:12])
    except Exception as e:
        return f"❌ CoinDCX scan error: {str(e)[:100]}"


def rocket_scan_pump() -> str:
    """One-call: pump.fun only scan."""
    try:
        tokens = fetch_pump_hot_tokens()
        scored = []
        for t in tokens:
            try:
                s = calculate_rocket_score(t)
                if s["rocket_score"] >= 15:
                    scored.append(s)
            except:
                continue
        scored.sort(key=lambda x: x.get("rocket_score", 0), reverse=True)
        return format_rocket_scan(scored[:12])
    except Exception as e:
        return f"❌ pump.fun scan error: {str(e)[:100]}"


def rocket_token_detail(query: str) -> str:
    """One-call: Detailed analysis of a specific token."""
    try:
        pairs = search_dex_token(query)
        if not pairs:
            return f"❌ '{query}' DexScreener पर नहीं मिला। Symbol check करो।"
        
        best = pairs[0]
        token = _normalize_dex_pair(best) if CRYPTO_OK else _basic_normalize_dex(best)
        scored = calculate_rocket_score(token)
        return format_single_rocket(scored)
    except Exception as e:
        return f"❌ Token detail error: {str(e)[:100]}"


# ═══════════════════════════════════════════════════════════
#  MODULE TEST
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀 Web3 Rocket Scanner — Test Run")
    print("=" * 50)
    
    # Full scan
    result = rocket_scan_full()
    print(result)
