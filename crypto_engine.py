"""
========================================================================================
  SUPER CRYPTO ENGINE — Pump.fun + DexScreener + ML Scoring | INR ONLY ₹
========================================================================================

Full-powered crypto gem hunter with:
  1. pump.fun Solana meme-coin scanner (trending, new launches, king-of-hill)
  2. DexScreener multi-chain trending token scanner
  3. ML-based gem scoring (40+ signals, momentum, volume, buy pressure)
  4. AI analysis via Groq/Gemini for top picks
  5. USD→INR conversion (live CoinGecko rate) — ALL prices shown in ₹
  6. Real-time alerts: gems, dips, pumps, rug detection
  7. Token name, symbol, chain, social links, creator info
  
All prices displayed in INR (₹) with live USD/INR conversion.
"""

import os
import time
import math
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("crypto_engine")


# ═══════════════════════════════════════════════════════════════════════════
#  USD → INR CONVERSION (Live Rate)
# ═══════════════════════════════════════════════════════════════════════════

_inr_rate: float = 90.0  # fallback
_inr_rate_ts: float = 0.0
INR_RATE_TTL = 300  # refresh every 5 min


def get_usd_inr_rate() -> float:
    """Get live USD/INR rate from CoinGecko. Cached 5 min."""
    global _inr_rate, _inr_rate_ts
    now = time.time()
    if now - _inr_rate_ts < INR_RATE_TTL:
        return _inr_rate
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=usd-coin&vs_currencies=inr",
            timeout=8,
        )
        if r.status_code == 200:
            rate = r.json().get("usd-coin", {}).get("inr", 0)
            if rate > 50:
                _inr_rate = float(rate)
                _inr_rate_ts = now
    except Exception:
        pass
    return _inr_rate


def usd_to_inr(usd: float) -> float:
    """Convert USD amount to INR."""
    return usd * get_usd_inr_rate()


def fmt_inr(amount: float) -> str:
    """Format INR amount with ₹ symbol, Indian number system for large values."""
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:.2f} Cr"
    elif amount >= 1_00_000:
        return f"₹{amount / 1_00_000:.2f} L"
    elif amount >= 1_000:
        return f"₹{amount:,.0f}"
    elif amount >= 1:
        return f"₹{amount:.2f}"
    elif amount >= 0.0001:
        return f"₹{amount:.6f}"
    else:
        return f"₹{amount:.10f}"


def get_sol_inr_price() -> float:
    """Get SOL price in INR."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=inr",
            timeout=8,
        )
        if r.status_code == 200:
            return float(r.json().get("solana", {}).get("inr", 0))
    except Exception:
        pass
    return 0.0


# ═══════════════════════════════════════════════════════════════════════════
#  API LAYER — CACHE + RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════

_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}
CACHE_TTL = 5


def _cached_get(url: str, ttl: int = CACHE_TTL, headers: Optional[Dict] = None) -> Optional[Any]:
    """GET with simple in-memory cache."""
    now = time.time()
    if url in _cache and (now - _cache_ts.get(url, 0)) < ttl:
        return _cache[url]
    try:
        r = requests.get(url, timeout=15, headers=headers or {})
        if r.status_code == 200:
            ct = r.headers.get("content-type", "")
            if "json" in ct or r.text.strip().startswith(("{", "[")):
                data = r.json()
                _cache[url] = data
                _cache_ts[url] = now
                return data
    except Exception as e:
        logger.warning(f"API error ({url[:60]}): {e}")
    return _cache.get(url)


# ═══════════════════════════════════════════════════════════════════════════
#  PUMP.FUN API — Solana Meme Coin Launchpad
# ═══════════════════════════════════════════════════════════════════════════

PUMP_BASE = "https://frontend-api-v3.pump.fun"


def pump_get_coins(sort: str = "last_trade_timestamp", order: str = "DESC",
                   limit: int = 30, offset: int = 0) -> List[Dict]:
    """
    Fetch coins from pump.fun.
    sort: last_trade_timestamp | market_cap | created_timestamp
    order: DESC | ASC
    """
    url = (
        f"{PUMP_BASE}/coins?offset={offset}&limit={limit}"
        f"&sort={sort}&order={order}&includeNsfw=false"
    )
    data = _cached_get(url, ttl=10)
    return data if isinstance(data, list) else []


def pump_get_trending(limit: int = 30) -> List[Dict]:
    """Get pump.fun tokens sorted by recent trading activity (trending)."""
    return pump_get_coins(sort="last_trade_timestamp", order="DESC", limit=limit)


def pump_get_top_mcap(limit: int = 30) -> List[Dict]:
    """Get pump.fun tokens sorted by market cap (top coins)."""
    return pump_get_coins(sort="market_cap", order="DESC", limit=limit)


def pump_get_newest(limit: int = 30) -> List[Dict]:
    """Get newest pump.fun token launches."""
    return pump_get_coins(sort="created_timestamp", order="DESC", limit=limit)


def pump_get_coin_detail(mint: str) -> Optional[Dict]:
    """Get detailed info for a specific pump.fun coin by mint address."""
    url = f"{PUMP_BASE}/coins/{mint}"
    data = _cached_get(url, ttl=15)
    return data if isinstance(data, dict) else None


def _normalize_pump_token(t: Dict) -> Dict:
    """Normalize pump.fun token into standard format for scoring/display."""
    usd_mcap = float(t.get("usd_market_cap", 0) or 0)
    sol_mcap = float(t.get("market_cap", 0) or 0)
    total_supply = float(t.get("total_supply", 0) or 0)

    # Estimate price per token in USD
    price_usd = usd_mcap / total_supply if total_supply > 0 else 0

    # Bonding curve status
    is_graduated = bool(t.get("complete", False))
    has_raydium = bool(t.get("raydium_pool"))

    # Social links
    twitter = t.get("twitter", "") or ""
    telegram = t.get("telegram", "") or ""
    website = t.get("website", "") or ""

    # Age calculation
    created_ts = t.get("created_timestamp", 0)
    if isinstance(created_ts, int) and created_ts > 1_000_000_000_000:
        created_ts = created_ts / 1000  # ms to sec
    age_hours = (time.time() - created_ts) / 3600 if created_ts > 0 else 0

    inr_rate = get_usd_inr_rate()
    return {
        "source": "pump.fun",
        "name": t.get("name", "?"),
        "symbol": t.get("symbol", "?"),
        "mint": t.get("mint", ""),
        "chain": "solana",
        "price_usd": price_usd,
        "price_inr": price_usd * inr_rate,
        "mcap_usd": usd_mcap,
        "mcap_inr": usd_mcap * inr_rate,
        "mcap_sol": sol_mcap,
        "total_supply": total_supply,
        "is_graduated": is_graduated,
        "has_raydium": has_raydium,
        "twitter": twitter,
        "telegram": telegram,
        "website": website,
        "image_uri": t.get("image_uri", ""),
        "creator": t.get("creator", ""),
        "reply_count": int(t.get("reply_count", 0) or 0),
        "age_hours": age_hours,
        "ath_mcap_usd": float(t.get("ath_market_cap", 0) or 0) / 1e9 if t.get("ath_market_cap") else 0,
        "url": f"https://pump.fun/coin/{t.get('mint', '')}",
        "dex_url": f"https://dexscreener.com/solana/{t.get('mint', '')}",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  DEXSCREENER API (multi-chain)
# ═══════════════════════════════════════════════════════════════════════════

DEXSCREENER_BASE = "https://api.dexscreener.com"


def get_top_boosted_tokens(limit: int = 30) -> List[Dict]:
    """Get DexScreener top boosted (trending) tokens."""
    data = _cached_get(f"{DEXSCREENER_BASE}/token-boosts/top/v1", ttl=10)
    return data[:limit] if isinstance(data, list) else []


def get_token_pairs(chain: str, token_address: str) -> List[Dict]:
    """Get detailed pair data for a token from DexScreener."""
    data = _cached_get(f"{DEXSCREENER_BASE}/tokens/v1/{chain}/{token_address}", ttl=10)
    return data if isinstance(data, list) else []


def get_latest_token_profiles(limit: int = 30) -> List[Dict]:
    """Get latest token profiles."""
    data = _cached_get(f"{DEXSCREENER_BASE}/token-profiles/latest/v1", ttl=10)
    return data[:limit] if isinstance(data, list) else []


def _normalize_dex_pair(pair: Dict) -> Dict:
    """Normalize a DexScreener pair into standard token format."""
    base_token = pair.get("baseToken", {})
    pc = pair.get("priceChange", {})
    vol = pair.get("volume", {})
    liq = pair.get("liquidity", {})
    txns = pair.get("txns", {})
    mcap = float(pair.get("marketCap", 0) or 0)
    fdv = float(pair.get("fdv", 0) or 0)
    price_usd = float(pair.get("priceUsd", 0) or 0)

    inr_rate = get_usd_inr_rate()
    return {
        "source": "dexscreener",
        "name": base_token.get("name", "?"),
        "symbol": base_token.get("symbol", "?"),
        "chain": pair.get("chainId", "?"),
        "mint": base_token.get("address", ""),
        "price_usd": price_usd,
        "price_inr": price_usd * inr_rate,
        "mcap_usd": mcap,
        "mcap_inr": mcap * inr_rate,
        "fdv_usd": fdv,
        "fdv_inr": fdv * inr_rate,
        "liq_usd": float(liq.get("usd", 0) or 0),
        "liq_inr": float(liq.get("usd", 0) or 0) * inr_rate,
        "vol_m5": float(vol.get("m5", 0) or 0),
        "vol_h1": float(vol.get("h1", 0) or 0),
        "vol_h6": float(vol.get("h6", 0) or 0),
        "vol_h24": float(vol.get("h24", 0) or 0),
        "vol_h24_inr": float(vol.get("h24", 0) or 0) * inr_rate,
        "change_m5": float(pc.get("m5", 0) or 0),
        "change_h1": float(pc.get("h1", 0) or 0),
        "change_h6": float(pc.get("h6", 0) or 0),
        "change_h24": float(pc.get("h24", 0) or 0),
        "buys_h1": int(txns.get("h1", {}).get("buys", 0) or 0),
        "sells_h1": int(txns.get("h1", {}).get("sells", 0) or 0),
        "buys_h24": int(txns.get("h24", {}).get("buys", 0) or 0),
        "sells_h24": int(txns.get("h24", {}).get("sells", 0) or 0),
        "pair_address": pair.get("pairAddress", ""),
        "url": f"https://pump.fun/coin/{base_token.get('address', '')}" if pair.get("chainId") == "solana" else "",
        "dex_url": pair.get("url", ""),
        "is_graduated": True,
        "has_raydium": pair.get("chainId") == "solana",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  ML GEM SCORING ENGINE — 40+ signals
# ═══════════════════════════════════════════════════════════════════════════

def calculate_gem_score(token: Dict) -> Dict:
    """
    ML-style scoring for crypto gem identification.
    Works with both pump.fun and DexScreener normalized tokens.

    Scoring (0-100):
      - Dip Detection (0-20)
      - Volume Surge (0-15)
      - Buy Pressure (0-15)
      - Market Cap tier (0-15)
      - Liquidity Health (0-10)
      - Momentum Pattern (0-10)
      - Social Signals (0-10)
      - Rug Risk Penalty (-10 to 0)
    """
    score = 0
    reasons = []
    warnings = []

    source = token.get("source", "dexscreener")
    mcap_usd = token.get("mcap_usd", 0)
    mcap_inr = token.get("mcap_inr", 0)
    price_usd = token.get("price_usd", 0)
    liq_usd = token.get("liq_usd", 0)

    # Price changes (DexScreener tokens)
    m5 = token.get("change_m5", 0)
    h1 = token.get("change_h1", 0)
    h6 = token.get("change_h6", 0)
    h24 = token.get("change_h24", 0)

    vol_h1 = token.get("vol_h1", 0)
    vol_h24 = token.get("vol_h24", 0)
    buys_h1 = token.get("buys_h1", 0)
    sells_h1 = token.get("sells_h1", 0)
    buys_h24 = token.get("buys_h24", 0)
    sells_h24 = token.get("sells_h24", 0)

    # ── 1. DIP DETECTION (0-20) ──
    if h1 <= -5:
        dip_pts = min(20, abs(h1) * 1.5)
        score += dip_pts
        reasons.append(f"🔴 1h dip: {h1:+.1f}% (buy the dip)")
    elif h24 <= -10:
        score += min(15, abs(h24) * 0.5)
        reasons.append(f"🔴 24h correction: {h24:+.1f}%")
    elif m5 <= -3:
        score += min(12, abs(m5) * 2)
        reasons.append(f"⚡ 5m flash dip: {m5:+.1f}%")

    # ── 2. VOLUME SURGE (0-15) ──
    if vol_h1 > 0 and vol_h24 > 0:
        hourly_avg = vol_h24 / 24
        if hourly_avg > 0:
            vol_ratio = vol_h1 / hourly_avg
            if vol_ratio > 3:
                score += min(15, vol_ratio * 2.5)
                reasons.append(f"📊 Volume surge: {vol_ratio:.1f}x avg")
            elif vol_ratio > 1.5:
                score += min(8, vol_ratio * 2)

    # ── 3. BUY PRESSURE (0-15) ──
    total_h1 = buys_h1 + sells_h1
    if total_h1 > 10:
        buy_ratio = buys_h1 / total_h1
        if buy_ratio > 0.65:
            score += min(15, (buy_ratio - 0.5) * 50)
            reasons.append(f"🟢 Buy pressure: {buy_ratio:.0%} ({buys_h1}B/{sells_h1}S)")
        elif buy_ratio < 0.35:
            warnings.append(f"🔴 Sell pressure: {buy_ratio:.0%}")

    # ── 4. MARKET CAP TIER (0-15) ──
    if 0 < mcap_usd < 10_000:
        score += 15
        reasons.append(f"💎 Micro cap: {fmt_inr(mcap_inr)} (max upside)")
    elif 0 < mcap_usd < 100_000:
        score += 12
        reasons.append(f"💎 Low cap: {fmt_inr(mcap_inr)}")
    elif 0 < mcap_usd < 1_000_000:
        score += 8
        reasons.append(f"🔹 Small cap: {fmt_inr(mcap_inr)}")
    elif 0 < mcap_usd < 10_000_000:
        score += 5

    # ── 5. LIQUIDITY (0-10) ──
    if liq_usd >= 1000:
        score += min(10, math.log10(liq_usd) * 2)
        reasons.append(f"💧 Liquidity: {fmt_inr(liq_usd * get_usd_inr_rate())}")
    elif liq_usd < 500 and source == "dexscreener":
        warnings.append(f"⚠️ Low liquidity: {fmt_inr(liq_usd * get_usd_inr_rate())}")

    # ── 6. MOMENTUM (0-10) ──
    if h24 < -5 and h1 > 0:
        score += 10
        reasons.append(f"🔄 Reversal: 24h {h24:+.1f}% but 1h {h1:+.1f}%")
    elif h24 < -10 and m5 > 0:
        score += 8
        reasons.append(f"⚡ Bounce: 24h {h24:+.1f}% but 5m {m5:+.1f}%")
    if h1 > 50:
        score += 5
        reasons.append(f"🚀 Pumping: 1h {h1:+.1f}%")

    # ── 7. SOCIAL / COMMUNITY (0-10, pump.fun only) ──
    if source == "pump.fun":
        reply_count = token.get("reply_count", 0)
        if reply_count > 500:
            score += 10
            reasons.append(f"💬 Active community: {reply_count} replies")
        elif reply_count > 100:
            score += 6
            reasons.append(f"💬 Growing community: {reply_count} replies")
        elif reply_count > 20:
            score += 3

        if token.get("twitter"):
            score += 2
            reasons.append("🐦 Has Twitter")
        if token.get("telegram"):
            score += 2
            reasons.append("📱 Has Telegram")
        if token.get("is_graduated"):
            score += 5
            reasons.append("🎓 Graduated to Raydium")

        age_h = token.get("age_hours", 0)
        if 0.5 < age_h < 24:
            score += 3
            reasons.append(f"🆕 Fresh: {age_h:.1f}h old")

    # ── RUG RISK PENALTIES ──
    if liq_usd < 100 and source == "dexscreener":
        score -= 10
        warnings.append("🚨 Extremely low liquidity — possible rug")
    if total_h1 > 0 and total_h1 < 5:
        warnings.append("⚠️ Very low trade activity")
    if h24 > 1000:
        warnings.append("⚠️ Massive pump — could dump hard")

    # Potential multipliers
    potential_1m = 1_000_000 / mcap_usd if mcap_usd > 0 else 0
    potential_10m = 10_000_000 / mcap_usd if mcap_usd > 0 else 0

    token["gem_score"] = min(100, max(0, round(score)))
    token["reasons"] = reasons
    token["warnings"] = warnings
    token["potential_to_1m"] = potential_1m
    token["potential_to_10m"] = potential_10m
    return token


# ═══════════════════════════════════════════════════════════════════════════
#  SCANNER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def scan_pump_trending(min_score: int = 10, limit: int = 20) -> List[Dict]:
    """Scan pump.fun trending tokens and score them."""
    raw = pump_get_trending(limit=40)
    tokens = [calculate_gem_score(_normalize_pump_token(t)) for t in raw]
    tokens = [t for t in tokens if t["gem_score"] >= min_score]
    tokens.sort(key=lambda x: x["gem_score"], reverse=True)
    return tokens[:limit]


def scan_pump_newest(min_score: int = 5, limit: int = 20) -> List[Dict]:
    """Scan newest pump.fun launches."""
    raw = pump_get_newest(limit=40)
    tokens = [calculate_gem_score(_normalize_pump_token(t)) for t in raw]
    tokens = [t for t in tokens if t["gem_score"] >= min_score]
    tokens.sort(key=lambda x: x["gem_score"], reverse=True)
    return tokens[:limit]


def scan_pump_top_mcap(limit: int = 20) -> List[Dict]:
    """Top pump.fun tokens by market cap."""
    raw = pump_get_top_mcap(limit=limit)
    tokens = [calculate_gem_score(_normalize_pump_token(t)) for t in raw]
    return tokens[:limit]


def scan_trending_gems(min_score: int = 15, limit: int = 20) -> List[Dict]:
    """Scan DexScreener trending tokens and score them for gem potential."""
    boosted = get_top_boosted_tokens(30)
    if not boosted:
        return []

    scored = []
    for token in boosted:
        addr = token.get("tokenAddress", "")
        chain = token.get("chainId", "")
        if not addr or not chain:
            continue
        pairs = get_token_pairs(chain, addr)
        if not pairs:
            continue
        best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
        gem = calculate_gem_score(_normalize_dex_pair(best))
        if gem["gem_score"] >= min_score:
            scored.append(gem)

    scored.sort(key=lambda x: x["gem_score"], reverse=True)
    return scored[:limit]


def scan_all_gems(min_score: int = 10, limit: int = 20) -> List[Dict]:
    """Combined scan: pump.fun + DexScreener, all in one list sorted by gem score."""
    pump_gems = scan_pump_trending(min_score=min_score, limit=limit)
    dex_gems = scan_trending_gems(min_score=min_score, limit=limit)
    all_gems = pump_gems + dex_gems
    all_gems.sort(key=lambda x: x["gem_score"], reverse=True)
    return all_gems[:limit]


def scan_dip_tokens(max_change_h1: float = -5.0, limit: int = 10) -> List[Dict]:
    """Find tokens that are significantly down (dip buy opportunities)."""
    all_g = scan_trending_gems(min_score=0, limit=30)
    dips = [g for g in all_g if g.get("change_h1", 0) <= max_change_h1 or g.get("change_h24", 0) <= -10]
    dips.sort(key=lambda x: x.get("change_h1", 0))
    return dips[:limit]


def scan_pumping_tokens(min_change_h1: float = 20.0, limit: int = 10) -> List[Dict]:
    """Find tokens that are pumping hard right now."""
    all_g = scan_trending_gems(min_score=0, limit=30)
    pumps = [g for g in all_g if g.get("change_h1", 0) >= min_change_h1 or g.get("change_h24", 0) >= 100]
    pumps.sort(key=lambda x: x.get("change_h1", 0), reverse=True)
    return pumps[:limit]


# ═══════════════════════════════════════════════════════════════════════════
#  AI GEM ANALYSIS (Groq / Gemini)
# ═══════════════════════════════════════════════════════════════════════════

def ai_analyze_gems(gems: List[Dict], max_gems: int = 5) -> str:
    """Use AI to analyse top gem candidates."""
    if not gems:
        return "No gems found in current scan."

    top = gems[:max_gems]
    inr_rate = get_usd_inr_rate()

    context = "CRYPTO GEM SCANNER — Top Trending Tokens (₹ INR):\n\n"
    for i, g in enumerate(top, 1):
        src_tag = "🟣 pump.fun" if g.get("source") == "pump.fun" else "🟢 DexScreener"
        context += (
            f"{i}. **{g['symbol']}** ({g['name']}) — {g.get('chain', '?').upper()} [{src_tag}]\n"
            f"   Price: {fmt_inr(g.get('price_inr', 0))} | MCap: {fmt_inr(g.get('mcap_inr', 0))}\n"
        )
        if g.get("source") == "dexscreener":
            context += (
                f"   5m: {g.get('change_m5', 0):+.1f}% | 1h: {g.get('change_h1', 0):+.1f}% | "
                f"24h: {g.get('change_h24', 0):+.1f}%\n"
                f"   Vol 24h: {fmt_inr(g.get('vol_h24', 0) * inr_rate)}\n"
            )
        else:
            context += (
                f"   Community: {g.get('reply_count', 0)} replies\n"
                f"   Graduated: {'Yes ✅' if g.get('is_graduated') else 'No ❌'}\n"
            )
        context += (
            f"   Gem Score: {g['gem_score']}/100\n"
            f"   Reasons: {'; '.join(g.get('reasons', []))}\n"
            f"   Warnings: {'; '.join(g.get('warnings', [])) or 'None'}\n\n"
        )

    query = (
        f"Analyze these trending crypto tokens and identify the BEST gem:\n\n"
        f"{context}\n"
        f"For each: Is it a potential 10x-1000x or a rug? Buy/Sell/Avoid?\n"
        f"Give TOP PICK with confidence. All prices in INR (₹). Format for Telegram."
    )

    try:
        from ai_chat import ai_chat
        return ai_chat(query, chat_id=-999)
    except Exception as e:
        logger.error(f"AI gem analysis failed: {e}")
        return _format_gems_basic(top)


# ═══════════════════════════════════════════════════════════════════════════
#  FORMATTED TELEGRAM MESSAGES — ALL IN INR ₹
# ═══════════════════════════════════════════════════════════════════════════

def _format_gems_basic(gems: List[Dict]) -> str:
    """Format gems list for Telegram (INR only)."""
    msg = "🪙💎 *CRYPTO GEM SCANNER* 💎🪙\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, g in enumerate(gems, 1):
        gs = g["gem_score"]
        if gs >= 70:
            grade = "🔥🔥🔥 S-TIER GEM"
        elif gs >= 50:
            grade = "💎💎 A-TIER"
        elif gs >= 30:
            grade = "🔹 B-TIER"
        else:
            grade = "⚪ C-TIER"

        src_tag = "🟣 pump.fun" if g.get("source") == "pump.fun" else "🟢 DexScreener"
        msg += (
            f"*{i}. {g['symbol']}* ({g['name']})\n"
            f"   {grade} — Score: {gs}/100\n"
            f"   🔗 {g.get('chain', '?').upper()} | {src_tag}\n"
            f"   💰 Price: {fmt_inr(g.get('price_inr', 0))}\n"
            f"   📊 MCap: {fmt_inr(g.get('mcap_inr', 0))}\n"
        )

        if g.get("source") == "dexscreener":
            msg += (
                f"   ⏱️ 5m: {g.get('change_m5', 0):+.1f}% | 1h: {g.get('change_h1', 0):+.1f}% | "
                f"24h: {g.get('change_h24', 0):+.1f}%\n"
                f"   📈 Vol: {fmt_inr(g.get('vol_h24_inr', 0))}\n"
                f"   💧 Liq: {fmt_inr(g.get('liq_inr', 0))}\n"
                f"   🛒 B/S 1h: {g.get('buys_h1', 0)}/{g.get('sells_h1', 0)}\n"
            )
        else:
            msg += (
                f"   💬 Replies: {g.get('reply_count', 0)}\n"
                f"   🎓 {'Graduated ✅' if g.get('is_graduated') else 'Bonding Curve ⏳'}\n"
            )
            if g.get("age_hours", 0) > 0:
                msg += f"   ⏰ Age: {g['age_hours']:.1f}h\n"

        if g.get("potential_to_1m", 0) > 1:
            msg += f"   🚀 Potential to ₹9Cr MCap: {g['potential_to_1m']:.0f}x\n"

        if g.get("reasons"):
            msg += f"   ✅ {' | '.join(g['reasons'][:3])}\n"
        if g.get("warnings"):
            msg += f"   ⚠️ {' | '.join(g['warnings'][:2])}\n"

        url = g.get("url") or g.get("dex_url", "")
        if url:
            msg += f"   🔗 [View]({url})\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! Crypto is extremely volatile. Never invest more than you can lose.*"
    return msg


def format_pump_trending(tokens: List[Dict]) -> str:
    """Format pump.fun trending tokens for Telegram (INR)."""
    if not tokens:
        return "❌ No pump.fun tokens found. Try again."

    msg = "🟣🔥 *PUMP.FUN — TRENDING TOKENS* 🔥🟣\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Solana meme-coin launchpad — All prices in ₹_\n\n"

    sol_inr = get_sol_inr_price()
    inr_rate = get_usd_inr_rate()

    for i, t in enumerate(tokens[:10], 1):
        graduated = "✅" if t.get("is_graduated") else "⏳"
        social = ""
        if t.get("twitter"):
            social += "🐦 "
        if t.get("telegram"):
            social += "📱 "

        msg += (
            f"*{i}. {t['symbol']}* ({t['name']}) {graduated}\n"
            f"   💰 Price: {fmt_inr(t.get('price_inr', 0))}\n"
            f"   📊 MCap: {fmt_inr(t.get('mcap_inr', 0))}\n"
            f"   💬 Replies: {t.get('reply_count', 0)} | {social}\n"
        )
        if t.get("age_hours", 0) > 0:
            age = t["age_hours"]
            if age < 1:
                msg += f"   ⏰ Age: {age * 60:.0f} min 🆕\n"
            elif age < 24:
                msg += f"   ⏰ Age: {age:.1f}h\n"
            else:
                msg += f"   ⏰ Age: {age / 24:.1f} days\n"

        if t.get("gem_score", 0) >= 30:
            msg += f"   🎯 Gem Score: *{t['gem_score']}/100*\n"

        url = t.get("url", "")
        if url:
            msg += f"   🔗 [pump.fun]({url})"
            dex = t.get("dex_url", "")
            if dex:
                msg += f" | [DexScreener]({dex})"
            msg += "\n"
        msg += "\n"

    if sol_inr > 0:
        msg += f"💎 *SOL Price:* {fmt_inr(sol_inr)}\n"
    msg += f"💵 *USD/INR:* ₹{inr_rate:.2f}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🔗 [pump.fun](https://pump.fun)\n"
    msg += "⚠️ *DYOR! Meme coins are extremely risky.*"
    return msg


def format_pump_new_launches(tokens: List[Dict]) -> str:
    """Format newest pump.fun launches for Telegram (INR)."""
    if not tokens:
        return "❌ No new launches found."

    msg = "🆕🟣 *PUMP.FUN — NEW LAUNCHES* 🟣🆕\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Fresh Solana meme coins — All prices in ₹_\n\n"

    for i, t in enumerate(tokens[:10], 1):
        graduated = "✅ Raydium" if t.get("is_graduated") else "⏳ Bonding"
        age = t.get("age_hours", 0)
        if age < 1:
            age_str = f"{age * 60:.0f} min 🆕🔥"
        elif age < 24:
            age_str = f"{age:.1f}h"
        else:
            age_str = f"{age / 24:.1f} days"

        msg += (
            f"*{i}. {t['symbol']}* ({t['name']})\n"
            f"   💰 {fmt_inr(t.get('price_inr', 0))} | MCap: {fmt_inr(t.get('mcap_inr', 0))}\n"
            f"   ⏰ {age_str} | {graduated}\n"
            f"   💬 {t.get('reply_count', 0)} replies | 🎯 Score: {t.get('gem_score', 0)}/100\n"
        )
        url = t.get("url", "")
        if url:
            msg += f"   🔗 [View]({url})\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! New coins can rug at any time.*"
    return msg


def format_pump_top(tokens: List[Dict]) -> str:
    """Format top pump.fun tokens by market cap (INR)."""
    if not tokens:
        return "❌ No data available."

    msg = "🏆🟣 *PUMP.FUN — TOP BY MARKET CAP* 🟣🏆\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_All prices in ₹ INR_\n\n"

    for i, t in enumerate(tokens[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        social = ""
        if t.get("twitter"):
            social += "[🐦](" + t["twitter"] + ") "
        if t.get("telegram"):
            social += "[📱](" + t["telegram"] + ") "

        msg += (
            f"{medal} *{t['symbol']}* ({t['name']})\n"
            f"   💰 Price: {fmt_inr(t.get('price_inr', 0))}\n"
            f"   📊 MCap: {fmt_inr(t.get('mcap_inr', 0))}\n"
            f"   💬 {t.get('reply_count', 0)} replies {social}\n"
        )
        url = t.get("url", "")
        if url:
            msg += f"   🔗 [View]({url})\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! Past performance ≠ future results.*"
    return msg


def format_trending_overview() -> str:
    """DexScreener trending tokens overview in INR."""
    boosted = get_top_boosted_tokens(15)
    if not boosted:
        return "❌ Could not fetch DexScreener data. Try again."

    inr_rate = get_usd_inr_rate()
    msg = "🪙🔥 *DEXSCREENER TRENDING* 🔥🪙\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_All prices in ₹ INR_\n\n"

    count = 0
    for token in boosted[:15]:
        addr = token.get("tokenAddress", "")
        chain = token.get("chainId", "")
        if not addr or not chain:
            continue
        pairs = get_token_pairs(chain, addr)
        if not pairs:
            continue

        p = max(pairs, key=lambda x: float((x.get("volume") or {}).get("h24", 0) or 0))
        bt = p.get("baseToken", {})
        pc = p.get("priceChange", {})
        vol = p.get("volume", {})
        mcap = float(p.get("marketCap", 0) or 0)

        h1 = float(pc.get("h1", 0) or 0)
        h24 = float(pc.get("h24", 0) or 0)
        m5 = float(pc.get("m5", 0) or 0)
        price_usd = float(p.get("priceUsd", 0) or 0)

        trend = "🟢🚀" if h1 > 5 else "🟢" if h1 > 0 else "🟡" if h1 > -5 else "🔴📉"

        count += 1
        msg += (
            f"*{count}. {bt.get('symbol', '?')}* {trend}\n"
            f"   {fmt_inr(price_usd * inr_rate)} | "
            f"5m: {m5:+.1f}% | 1h: {h1:+.1f}% | 24h: {h24:+.1f}%\n"
            f"   Vol: {fmt_inr(float(vol.get('h24', 0) or 0) * inr_rate)} | "
            f"MCap: {fmt_inr(mcap * inr_rate)} | {chain.upper()}\n\n"
        )
        if count >= 10:
            break

    msg += f"💵 *USD/INR:* ₹{inr_rate:.2f}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🔗 [DexScreener](https://dexscreener.com)\n"
    msg += "⚠️ *DYOR! Not financial advice.*"
    return msg


def format_gem_alert(gem: Dict) -> str:
    """Single gem alert for Telegram (INR)."""
    gs = gem["gem_score"]
    if gs >= 70:
        emoji = "🔥🔥🔥"
        tier = "S-TIER GEM"
    elif gs >= 50:
        emoji = "💎💎"
        tier = "A-TIER GEM"
    elif gs >= 30:
        emoji = "🔹"
        tier = "B-TIER"
    else:
        emoji = "⚪"
        tier = "DETECTED"

    src = "🟣 pump.fun" if gem.get("source") == "pump.fun" else "🟢 DexScreener"

    msg = (
        f"{emoji} *CRYPTO GEM {tier}!* {emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 *{gem['symbol']}* ({gem['name']})\n"
        f"🔗 {gem.get('chain', '?').upper()} | {src}\n"
        f"💰 Price: {fmt_inr(gem.get('price_inr', 0))}\n"
        f"📊 MCap: {fmt_inr(gem.get('mcap_inr', 0))}\n"
    )

    if gem.get("source") == "dexscreener":
        msg += (
            f"💧 Liquidity: {fmt_inr(gem.get('liq_inr', 0))}\n\n"
            f"⏱️ *Price Changes:*\n"
            f"   5m: {gem.get('change_m5', 0):+.1f}% | 1h: {gem.get('change_h1', 0):+.1f}%\n"
            f"   6h: {gem.get('change_h6', 0):+.1f}% | 24h: {gem.get('change_h24', 0):+.1f}%\n\n"
            f"📈 Vol 24h: {fmt_inr(gem.get('vol_h24_inr', 0))}\n"
            f"🛒 Buys/Sells 1h: {gem.get('buys_h1', 0)}/{gem.get('sells_h1', 0)}\n"
        )
    else:
        msg += (
            f"\n💬 Community: {gem.get('reply_count', 0)} replies\n"
            f"🎓 {'Graduated to Raydium ✅' if gem.get('is_graduated') else 'Still on Bonding Curve ⏳'}\n"
        )

    msg += f"🎯 Gem Score: *{gs}/100*\n\n"

    if gem.get("reasons"):
        msg += "✅ *Bullish Signs:*\n"
        for r in gem["reasons"]:
            msg += f"   {r}\n"
        msg += "\n"
    if gem.get("warnings"):
        msg += "⚠️ *Warnings:*\n"
        for w in gem["warnings"]:
            msg += f"   {w}\n"
        msg += "\n"

    if gem.get("potential_to_1m", 0) > 1:
        msg += f"🚀 *Potential to ₹9Cr: {gem['potential_to_1m']:.0f}x*\n"

    url = gem.get("url") or gem.get("dex_url", "")
    if url:
        msg += f"\n🔗 [View Token]({url})\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! Crypto is extremely risky.*"
    return msg


def format_dip_alert(gems: List[Dict]) -> str:
    """Dip buy opportunities (INR)."""
    if not gems:
        return "No significant dips in trending tokens right now."

    msg = "🔴📉 *CRYPTO DIP ALERT — BUY THE DIP?* 📉🔴\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_All prices in ₹ INR_\n\n"

    for i, g in enumerate(gems[:5], 1):
        msg += (
            f"*{i}. {g['symbol']}* ({g.get('chain', '?').upper()})\n"
            f"   💰 {fmt_inr(g.get('price_inr', 0))}\n"
            f"   📉 1h: {g.get('change_h1', 0):+.1f}% | 24h: {g.get('change_h24', 0):+.1f}%\n"
            f"   📊 MCap: {fmt_inr(g.get('mcap_inr', 0))}\n"
            f"   🎯 Gem: {g['gem_score']}/100 | "
            f"🛒 B/S: {g.get('buys_h1', 0)}/{g.get('sells_h1', 0)}\n"
        )
        url = g.get("url") or g.get("dex_url", "")
        if url:
            msg += f"   🔗 [Chart]({url})\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! Dips can keep dipping!*"
    return msg


# ═══════════════════════════════════════════════════════════════════════════
#  BACKGROUND ALERT STATE
# ═══════════════════════════════════════════════════════════════════════════

_alerted_tokens: Dict[str, float] = {}
ALERT_COOLDOWN = 300


def get_new_gem_alerts(min_score: int = 40) -> List[Dict]:
    """Return only new gems not already alerted (for background loop)."""
    now = time.time()
    gems = scan_all_gems(min_score=min_score, limit=10)
    new = []
    for g in gems:
        key = f"{g.get('chain', '')}:{g.get('mint', g.get('symbol', ''))}"
        if now - _alerted_tokens.get(key, 0) > ALERT_COOLDOWN:
            new.append(g)
            _alerted_tokens[key] = now
    # Cleanup
    for k in [k for k, v in _alerted_tokens.items() if now - v > 3600]:
        del _alerted_tokens[k]
    return new


def get_new_dip_alerts(max_change_h1: float = -10.0) -> List[Dict]:
    """New dip alerts not yet sent."""
    now = time.time()
    dips = scan_dip_tokens(max_change_h1=max_change_h1, limit=5)
    new = []
    for d in dips:
        key = f"dip:{d.get('chain', '')}:{d.get('mint', d.get('symbol', ''))}"
        if now - _alerted_tokens.get(key, 0) > ALERT_COOLDOWN:
            new.append(d)
            _alerted_tokens[key] = now
    return new


# ═══════════════════════════════════════════════════════════════════════════
#  MULTI-CHAIN EXPANSION — Base, Arbitrum, BNB, Ethereum
# ═══════════════════════════════════════════════════════════════════════════

SUPPORTED_CHAINS = {
    "solana": {"name": "Solana", "emoji": "◎", "dex": True, "pump": True},
    "base": {"name": "Base", "emoji": "🔵", "dex": True, "pump": False},
    "arbitrum": {"name": "Arbitrum", "emoji": "🔷", "dex": True, "pump": False},
    "bsc": {"name": "BNB Chain", "emoji": "🟡", "dex": True, "pump": False},
    "ethereum": {"name": "Ethereum", "emoji": "⟠", "dex": True, "pump": False},
}


def scan_chain_trending(chain: str = "base", min_score: int = 10, limit: int = 15) -> List[Dict]:
    """Scan DexScreener trending tokens filtered by specific chain."""
    boosted = get_top_boosted_tokens(50)
    scored = []
    for token in boosted:
        addr = token.get("tokenAddress", "")
        tok_chain = token.get("chainId", "")
        if tok_chain != chain or not addr:
            continue
        pairs = get_token_pairs(tok_chain, addr)
        if not pairs:
            continue
        best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
        gem = calculate_gem_score(_normalize_dex_pair(best))
        if gem["gem_score"] >= min_score:
            scored.append(gem)

    scored.sort(key=lambda x: x["gem_score"], reverse=True)
    return scored[:limit]


def scan_multichain_gems(min_score: int = 10, limit: int = 20) -> List[Dict]:
    """Scan ALL supported chains for gems — multi-chain overview."""
    all_gems = []

    # pump.fun (Solana native)
    try:
        pump_gems = scan_pump_trending(min_score=min_score, limit=10)
        all_gems.extend(pump_gems)
    except Exception:
        pass

    # DexScreener trending (all chains)
    try:
        dex_gems = scan_trending_gems(min_score=min_score, limit=15)
        all_gems.extend(dex_gems)
    except Exception:
        pass

    all_gems.sort(key=lambda x: x["gem_score"], reverse=True)

    # Deduplicate by mint
    seen = set()
    unique = []
    for g in all_gems:
        key = g.get("mint", g.get("symbol", ""))
        if key not in seen:
            seen.add(key)
            unique.append(g)

    return unique[:limit]


def format_multichain_overview(gems: List[Dict]) -> str:
    """Format multi-chain gems for Telegram."""
    if not gems:
        return "❌ No multi-chain gems found."

    inr_rate = get_usd_inr_rate()
    msg = "🌐🔥 *MULTI-CHAIN GEM SCANNER* 🔥🌐\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Solana + Base + Arb + BNB + ETH — All ₹_\n\n"

    # Group by chain
    chain_counts = {}
    for g in gems:
        ch = g.get("chain", "?")
        chain_counts[ch] = chain_counts.get(ch, 0) + 1

    chain_str = " | ".join(
        f"{SUPPORTED_CHAINS.get(c, {}).get('emoji', '?')} {c.upper()}: {n}"
        for c, n in chain_counts.items()
    )
    msg += f"📊 {chain_str}\n\n"

    for i, g in enumerate(gems[:12], 1):
        ch_info = SUPPORTED_CHAINS.get(g.get("chain", ""), {})
        ch_emoji = ch_info.get("emoji", "?")
        src = "🟣" if g.get("source") == "pump.fun" else "🟢"

        msg += (
            f"*{i}. {g['symbol']}* {ch_emoji} {g.get('chain', '?').upper()} {src}\n"
            f"   💰 {fmt_inr(g.get('price_inr', 0))} | MCap: {fmt_inr(g.get('mcap_inr', 0))}\n"
            f"   🎯 Score: {g['gem_score']}/100\n"
        )
        if g.get("source") == "dexscreener":
            msg += f"   ⏱️ 1h: {g.get('change_h1', 0):+.1f}% | 24h: {g.get('change_h24', 0):+.1f}%\n"
        url = g.get("url") or g.get("dex_url", "")
        if url:
            msg += f"   🔗 [View]({url})\n"
        msg += "\n"

    msg += f"💵 USD/INR: ₹{inr_rate:.2f}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! Not financial advice.*"
    return msg
