"""
Crypto Gem Hunter Engine — DexScreener integration with AI/ML analysis.

Fetches trending tokens from DexScreener, analyzes them using ML scoring
and AI (Groq/Gemini), and identifies potential gem tokens that are dipped
but have explosive potential.

Features:
- Real-time DexScreener trending token data
- ML-based gem scoring (liquidity, volume, buy pressure, dip detection)
- AI analysis of top gems via Groq/Gemini
- Continuous monitoring with smart alerts
"""

import os
import time
import logging
import requests
import math
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("crypto_engine")

# ═══════════════════════════════════════════════════════════
#  DEXSCREENER API
# ═══════════════════════════════════════════════════════════

DEXSCREENER_BASE = "https://api.dexscreener.com"

# Cache to avoid hammering the API
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}
CACHE_TTL = 5  # seconds


def _cached_get(url: str, ttl: int = CACHE_TTL) -> Optional[Any]:
    """GET with simple in-memory cache."""
    now = time.time()
    if url in _cache and (now - _cache_ts.get(url, 0)) < ttl:
        return _cache[url]

    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            _cache[url] = data
            _cache_ts[url] = now
            return data
    except Exception as e:
        logger.warning(f"DexScreener API error: {e}")
    return _cache.get(url)  # return stale if available


def get_top_boosted_tokens(limit: int = 30) -> List[Dict]:
    """Get top boosted tokens from DexScreener (trending by boost score)."""
    data = _cached_get(f"{DEXSCREENER_BASE}/token-boosts/top/v1", ttl=10)
    if not data or not isinstance(data, list):
        return []
    return data[:limit]


def get_token_pairs(chain: str, token_address: str) -> List[Dict]:
    """Get detailed pair data for a token."""
    data = _cached_get(f"{DEXSCREENER_BASE}/tokens/v1/{chain}/{token_address}", ttl=10)
    if not data or not isinstance(data, list):
        return []
    return data


def get_latest_token_profiles(limit: int = 30) -> List[Dict]:
    """Get latest token profiles."""
    data = _cached_get(f"{DEXSCREENER_BASE}/token-profiles/latest/v1", ttl=10)
    if not data or not isinstance(data, list):
        return []
    return data[:limit]


# ═══════════════════════════════════════════════════════════
#  ML GEM SCORING — identifies potential moonshots
# ═══════════════════════════════════════════════════════════

def calculate_gem_score(pair: Dict) -> Dict:
    """
    ML-style scoring to identify potential gem tokens.
    
    Scores based on:
    - Dip detection (is the token down? lower = better for entry)
    - Volume surge (high volume = interest)
    - Buy/Sell ratio (more buys = accumulation)
    - Liquidity health (some liquidity needed, but not too much)
    - Market cap (lower = more upside potential)
    - Price momentum (5m, 1h, 6h, 24h trends)
    
    Returns score 0-100 where higher = better gem potential.
    """
    score = 0
    reasons = []
    warnings = []

    base_token = pair.get("baseToken", {})
    price_change = pair.get("priceChange", {})
    volume = pair.get("volume", {})
    liquidity = pair.get("liquidity", {})
    txns = pair.get("txns", {})
    mcap = pair.get("marketCap", 0) or 0
    fdv = pair.get("fdv", 0) or 0
    price_usd = float(pair.get("priceUsd", 0) or 0)

    # Time periods
    m5 = float(price_change.get("m5", 0) or 0)
    h1 = float(price_change.get("h1", 0) or 0)
    h6 = float(price_change.get("h6", 0) or 0)
    h24 = float(price_change.get("h24", 0) or 0)

    vol_m5 = float(volume.get("m5", 0) or 0)
    vol_h1 = float(volume.get("h1", 0) or 0)
    vol_h6 = float(volume.get("h6", 0) or 0)
    vol_h24 = float(volume.get("h24", 0) or 0)

    liq_usd = float(liquidity.get("usd", 0) or 0)

    buys_h1 = int(txns.get("h1", {}).get("buys", 0) or 0)
    sells_h1 = int(txns.get("h1", {}).get("sells", 0) or 0)
    buys_h24 = int(txns.get("h24", {}).get("buys", 0) or 0)
    sells_h24 = int(txns.get("h24", {}).get("sells", 0) or 0)

    # ── 1. DIP DETECTION (0-25 pts) ──
    # Tokens that are down are better entry points
    if h1 <= -5:
        dip_score = min(25, abs(h1) * 1.5)
        score += dip_score
        reasons.append(f"🔴 1h dip: {h1:+.1f}% (buy the dip)")
    elif h24 <= -10:
        dip_score = min(20, abs(h24) * 0.5)
        score += dip_score
        reasons.append(f"🔴 24h dip: {h24:+.1f}% (recovery play)")
    elif m5 <= -3:
        score += min(15, abs(m5) * 2)
        reasons.append(f"⚡ 5m flash dip: {m5:+.1f}%")

    # ── 2. VOLUME SURGE (0-20 pts) ──
    if vol_h1 > 0 and vol_h24 > 0:
        hourly_avg = vol_h24 / 24
        if hourly_avg > 0:
            vol_ratio = vol_h1 / hourly_avg
            if vol_ratio > 3:
                score += min(20, vol_ratio * 3)
                reasons.append(f"📊 Volume surge: {vol_ratio:.1f}x avg")
            elif vol_ratio > 1.5:
                score += min(10, vol_ratio * 2)
                reasons.append(f"📊 Rising volume: {vol_ratio:.1f}x avg")

    # ── 3. BUY PRESSURE (0-20 pts) ──
    total_h1 = buys_h1 + sells_h1
    if total_h1 > 10:
        buy_ratio = buys_h1 / total_h1
        if buy_ratio > 0.65:
            score += min(20, (buy_ratio - 0.5) * 60)
            reasons.append(f"🟢 Buy pressure: {buy_ratio:.0%} buys ({buys_h1}B/{sells_h1}S)")
        elif buy_ratio < 0.35:
            warnings.append(f"🔴 Sell pressure: {buy_ratio:.0%} buys")

    # ── 4. MARKET CAP — LOW = MORE UPSIDE (0-15 pts) ──
    if 0 < mcap < 10_000:
        score += 15
        reasons.append(f"💎 Micro cap: ${mcap:,.0f} (max upside)")
    elif 0 < mcap < 100_000:
        score += 12
        reasons.append(f"💎 Low cap: ${mcap:,.0f}")
    elif 0 < mcap < 1_000_000:
        score += 8
        reasons.append(f"🔹 Small cap: ${mcap:,.0f}")
    elif 0 < mcap < 10_000_000:
        score += 5
        reasons.append(f"🔹 Mid cap: ${mcap:,.0f}")

    # ── 5. LIQUIDITY HEALTH (0-10 pts) ──
    if liq_usd >= 1000:
        score += min(10, math.log10(liq_usd) * 2)
        reasons.append(f"💧 Liquidity: ${liq_usd:,.0f}")
    elif liq_usd < 500:
        warnings.append(f"⚠️ Low liquidity: ${liq_usd:,.0f}")

    # ── 6. MOMENTUM PATTERN (0-10 pts) ──
    # Ideal: 24h down but 5m/1h recovering (reversal pattern)
    if h24 < -5 and h1 > 0:
        score += 10
        reasons.append(f"🔄 Reversal: 24h {h24:+.1f}% but 1h {h1:+.1f}%")
    elif h24 < -10 and m5 > 0:
        score += 8
        reasons.append(f"⚡ Bounce: 24h {h24:+.1f}% but 5m {m5:+.1f}%")
    # Already pumping
    if h1 > 50:
        score += 5
        reasons.append(f"🚀 Pumping: 1h {h1:+.1f}%")
    if h24 > 100:
        score += 5
        reasons.append(f"🚀🚀 24h rocket: {h24:+.1f}%")

    # ── RISK FLAGS ──
    if liq_usd < 100:
        warnings.append("🚨 Extremely low liquidity — possible rug")
    if total_h1 < 5:
        warnings.append("⚠️ Very low activity")
    if h24 > 1000:
        warnings.append("⚠️ Massive pump — could dump")

    # Potential multiplier estimate
    if mcap > 0:
        potential_1m = 1_000_000 / mcap
        potential_10m = 10_000_000 / mcap
    else:
        potential_1m = 0
        potential_10m = 0

    return {
        "symbol": base_token.get("symbol", "?"),
        "name": base_token.get("name", "?"),
        "chain": pair.get("chainId", "?"),
        "price_usd": price_usd,
        "mcap": mcap,
        "fdv": fdv,
        "liquidity_usd": liq_usd,
        "volume_h24": vol_h24,
        "volume_h1": vol_h1,
        "change_m5": m5,
        "change_h1": h1,
        "change_h6": h6,
        "change_h24": h24,
        "buys_h1": buys_h1,
        "sells_h1": sells_h1,
        "buys_h24": buys_h24,
        "sells_h24": sells_h24,
        "gem_score": min(100, round(score)),
        "reasons": reasons,
        "warnings": warnings,
        "potential_to_1m": potential_1m,
        "potential_to_10m": potential_10m,
        "pair_address": pair.get("pairAddress", ""),
        "dex_url": pair.get("url", ""),
        "token_address": base_token.get("address", ""),
    }


# ═══════════════════════════════════════════════════════════
#  TRENDING TOKEN SCANNER
# ═══════════════════════════════════════════════════════════

def scan_trending_gems(min_score: int = 15, limit: int = 20) -> List[Dict]:
    """
    Scan DexScreener trending tokens and score them for gem potential.
    Returns top gems sorted by score (highest first).
    """
    boosted = get_top_boosted_tokens(30)
    if not boosted:
        return []

    scored_tokens = []

    for token in boosted:
        addr = token.get("tokenAddress", "")
        chain = token.get("chainId", "")
        if not addr or not chain:
            continue

        pairs = get_token_pairs(chain, addr)
        if not pairs:
            continue

        # Take the highest-volume pair
        best_pair = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
        gem = calculate_gem_score(best_pair)

        if gem["gem_score"] >= min_score:
            scored_tokens.append(gem)

    # Sort by gem score descending
    scored_tokens.sort(key=lambda x: x["gem_score"], reverse=True)
    return scored_tokens[:limit]


def scan_dip_tokens(max_change_h1: float = -5.0, limit: int = 10) -> List[Dict]:
    """Find tokens that are significantly down (dip buy opportunities)."""
    all_gems = scan_trending_gems(min_score=0, limit=30)
    dips = [g for g in all_gems if g["change_h1"] <= max_change_h1 or g["change_h24"] <= -10]
    dips.sort(key=lambda x: x["change_h1"])  # most dipped first
    return dips[:limit]


def scan_pumping_tokens(min_change_h1: float = 20.0, limit: int = 10) -> List[Dict]:
    """Find tokens that are pumping hard right now."""
    all_gems = scan_trending_gems(min_score=0, limit=30)
    pumps = [g for g in all_gems if g["change_h1"] >= min_change_h1 or g["change_h24"] >= 100]
    pumps.sort(key=lambda x: x["change_h1"], reverse=True)
    return pumps[:limit]


# ═══════════════════════════════════════════════════════════
#  AI GEM ANALYSIS (Groq / Gemini)
# ═══════════════════════════════════════════════════════════

def ai_analyze_gems(gems: List[Dict], max_gems: int = 5) -> str:
    """Use AI to provide detailed analysis of top gem candidates."""
    if not gems:
        return "No gems found in current scan."

    top = gems[:max_gems]

    # Build context for AI
    context = "CRYPTO GEM SCANNER — Top Trending Tokens from DexScreener:\n\n"
    for i, g in enumerate(top, 1):
        context += (
            f"{i}. **{g['symbol']}** ({g['name']}) — {g['chain'].upper()}\n"
            f"   Price: ${g['price_usd']:.10f} | MCap: ${g['mcap']:,.0f}\n"
            f"   5m: {g['change_m5']:+.1f}% | 1h: {g['change_h1']:+.1f}% | "
            f"6h: {g['change_h6']:+.1f}% | 24h: {g['change_h24']:+.1f}%\n"
            f"   Vol 24h: ${g['volume_h24']:,.0f} | Liq: ${g['liquidity_usd']:,.0f}\n"
            f"   Buys/Sells 1h: {g['buys_h1']}/{g['sells_h1']} | "
            f"24h: {g['buys_h24']}/{g['sells_h24']}\n"
            f"   Gem Score: {g['gem_score']}/100\n"
            f"   Reasons: {'; '.join(g['reasons'])}\n"
            f"   Warnings: {'; '.join(g['warnings']) if g['warnings'] else 'None'}\n"
            f"   Potential to $1M mcap: {g['potential_to_1m']:.0f}x\n\n"
        )

    query = (
        f"Analyze these trending crypto tokens from DexScreener and identify the BEST gem:\n\n"
        f"{context}\n"
        f"For each token, analyze:\n"
        f"1. Is this a potential 10x-1000x gem or a scam/rug?\n"
        f"2. What's the risk/reward ratio?\n"
        f"3. Is the dip a buying opportunity or a sign of dump?\n"
        f"4. Buy/Sell/Avoid recommendation\n"
        f"5. Suggested entry, target, and stop-loss\n\n"
        f"Give your TOP PICK with confidence level. Format for Telegram."
    )

    try:
        from ai_chat import ai_chat
        return ai_chat(query, chat_id=-999)
    except Exception as e:
        logger.error(f"AI gem analysis failed: {e}")
        return _format_gems_basic(top)


def _format_gems_basic(gems: List[Dict]) -> str:
    """Format gems without AI as fallback."""
    msg = "🪙💎 *CRYPTO GEM SCANNER* 💎🪙\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, g in enumerate(gems, 1):
        # Grade label
        if g["gem_score"] >= 70:
            grade = "🔥🔥🔥 S-TIER GEM"
        elif g["gem_score"] >= 50:
            grade = "💎💎 A-TIER"
        elif g["gem_score"] >= 30:
            grade = "🔹 B-TIER"
        else:
            grade = "⚪ C-TIER"

        msg += (
            f"*{i}. {g['symbol']}* ({g['name']})\n"
            f"   {grade} — Score: {g['gem_score']}/100\n"
            f"   🔗 Chain: {g['chain'].upper()}\n"
            f"   💰 Price: ${g['price_usd']:.10f}\n"
            f"   📊 MCap: ${g['mcap']:,.0f} | FDV: ${g['fdv']:,.0f}\n"
            f"   ⏱️ 5m: {g['change_m5']:+.1f}% | 1h: {g['change_h1']:+.1f}% | "
            f"24h: {g['change_h24']:+.1f}%\n"
            f"   📈 Vol 24h: ${g['volume_h24']:,.0f}\n"
            f"   💧 Liquidity: ${g['liquidity_usd']:,.0f}\n"
            f"   🛒 Buys/Sells 1h: {g['buys_h1']}/{g['sells_h1']}\n"
        )
        if g["potential_to_1m"] > 1:
            msg += f"   🚀 Potential to $1M: {g['potential_to_1m']:.0f}x\n"
        if g["reasons"]:
            msg += f"   ✅ {' | '.join(g['reasons'][:3])}\n"
        if g["warnings"]:
            msg += f"   ⚠️ {' | '.join(g['warnings'][:2])}\n"
        if g["dex_url"]:
            msg += f"   🔗 [DexScreener]({g['dex_url']})\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! Crypto is extremely volatile. Never invest more than you can lose.*"
    return msg


# ═══════════════════════════════════════════════════════════
#  FORMATTED OUTPUTS FOR TELEGRAM
# ═══════════════════════════════════════════════════════════

def format_trending_overview() -> str:
    """Quick overview of DexScreener trending tokens."""
    boosted = get_top_boosted_tokens(15)
    if not boosted:
        return "❌ Could not fetch DexScreener data. Try again."

    msg = "🪙🔥 *DEXSCREENER TRENDING* 🔥🪙\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

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
        liq = p.get("liquidity", {})
        mcap = p.get("marketCap", 0) or 0

        h1 = float(pc.get("h1", 0) or 0)
        h24 = float(pc.get("h24", 0) or 0)
        m5 = float(pc.get("m5", 0) or 0)

        # Direction emoji
        if h1 > 5:
            trend = "🟢🚀"
        elif h1 > 0:
            trend = "🟢"
        elif h1 > -5:
            trend = "🟡"
        else:
            trend = "🔴📉"

        count += 1
        msg += (
            f"*{count}. {bt.get('symbol', '?')}* {trend}\n"
            f"   ${float(p.get('priceUsd', 0) or 0):.8f} | "
            f"5m: {m5:+.1f}% | 1h: {h1:+.1f}% | 24h: {h24:+.1f}%\n"
            f"   Vol: ${float(vol.get('h24', 0) or 0):,.0f} | "
            f"MCap: ${mcap:,.0f} | {chain.upper()}\n\n"
        )

        if count >= 10:
            break

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🔗 [DexScreener Trending](https://dexscreener.com/?rankBy=trendingScoreM5&order=desc)\n"
    msg += "⚠️ *DYOR! Not financial advice.*"
    return msg


def format_gem_alert(gem: Dict) -> str:
    """Format a single gem alert for Telegram notification."""
    if gem["gem_score"] >= 70:
        emoji = "🔥🔥🔥"
        tier = "S-TIER GEM"
    elif gem["gem_score"] >= 50:
        emoji = "💎💎"
        tier = "A-TIER GEM"
    elif gem["gem_score"] >= 30:
        emoji = "🔹"
        tier = "B-TIER"
    else:
        emoji = "⚪"
        tier = "DETECTED"

    msg = (
        f"{emoji} *CRYPTO GEM {tier}!* {emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 *{gem['symbol']}* ({gem['name']})\n"
        f"🔗 Chain: {gem['chain'].upper()}\n"
        f"💰 Price: ${gem['price_usd']:.10f}\n"
        f"📊 MCap: ${gem['mcap']:,.0f}\n"
        f"💧 Liquidity: ${gem['liquidity_usd']:,.0f}\n\n"
        f"⏱️ *Price Changes:*\n"
        f"   5m: {gem['change_m5']:+.1f}% | 1h: {gem['change_h1']:+.1f}%\n"
        f"   6h: {gem['change_h6']:+.1f}% | 24h: {gem['change_h24']:+.1f}%\n\n"
        f"📈 Vol 24h: ${gem['volume_h24']:,.0f}\n"
        f"🛒 Buys/Sells 1h: {gem['buys_h1']}/{gem['sells_h1']}\n"
        f"🎯 Gem Score: *{gem['gem_score']}/100*\n\n"
    )

    if gem["reasons"]:
        msg += "✅ *Bullish Signs:*\n"
        for r in gem["reasons"]:
            msg += f"   {r}\n"
        msg += "\n"

    if gem["warnings"]:
        msg += "⚠️ *Warnings:*\n"
        for w in gem["warnings"]:
            msg += f"   {w}\n"
        msg += "\n"

    if gem["potential_to_1m"] > 1:
        msg += f"🚀 *Potential to $1M MCap: {gem['potential_to_1m']:.0f}x*\n"
    if gem["potential_to_10m"] > 1:
        msg += f"🚀🚀 *Potential to $10M MCap: {gem['potential_to_10m']:.0f}x*\n"

    msg += f"\n🔗 [View on DexScreener]({gem['dex_url']})\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *DYOR! Crypto is extremely risky.*"
    return msg


def format_dip_alert(gems: List[Dict]) -> str:
    """Format dip buy opportunities."""
    if not gems:
        return "No significant dips detected in trending tokens right now."

    msg = "🔴📉 *CRYPTO DIP ALERT — BUY THE DIP?* 📉🔴\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, g in enumerate(gems[:5], 1):
        msg += (
            f"*{i}. {g['symbol']}* ({g['chain'].upper()})\n"
            f"   💰 ${g['price_usd']:.10f}\n"
            f"   📉 1h: {g['change_h1']:+.1f}% | 24h: {g['change_h24']:+.1f}%\n"
            f"   📊 MCap: ${g['mcap']:,.0f} | Vol: ${g['volume_h24']:,.0f}\n"
            f"   🎯 Gem: {g['gem_score']}/100 | "
            f"🛒 B/S: {g['buys_h1']}/{g['sells_h1']}\n"
        )
        if g["dex_url"]:
            msg += f"   🔗 [Chart]({g['dex_url']})\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🔗 [DexScreener](https://dexscreener.com/?rankBy=trendingScoreM5&order=desc)\n"
    msg += "⚠️ *DYOR! Dips can keep dipping!*"
    return msg


# ═══════════════════════════════════════════════════════════
#  CRYPTO MONITORING STATE (for alert loop)
# ═══════════════════════════════════════════════════════════

# Track previously alerted tokens to avoid spam
_alerted_tokens: Dict[str, float] = {}
ALERT_COOLDOWN = 300  # 5 minutes before re-alerting same token


def get_new_gem_alerts(min_score: int = 40) -> List[Dict]:
    """
    Scan for gems and return only NEW ones (not already alerted).
    Used by the background alert loop.
    """
    now = time.time()
    gems = scan_trending_gems(min_score=min_score, limit=10)

    new_gems = []
    for g in gems:
        key = f"{g['chain']}:{g['token_address']}"
        last_alert = _alerted_tokens.get(key, 0)
        if now - last_alert > ALERT_COOLDOWN:
            new_gems.append(g)
            _alerted_tokens[key] = now

    # Cleanup old entries
    expired = [k for k, v in _alerted_tokens.items() if now - v > 3600]
    for k in expired:
        del _alerted_tokens[k]

    return new_gems


def get_new_dip_alerts(max_change_h1: float = -10.0) -> List[Dict]:
    """Find new significant dips not yet alerted."""
    now = time.time()
    dips = scan_dip_tokens(max_change_h1=max_change_h1, limit=5)

    new_dips = []
    for d in dips:
        key = f"dip:{d['chain']}:{d['token_address']}"
        last_alert = _alerted_tokens.get(key, 0)
        if now - last_alert > ALERT_COOLDOWN:
            new_dips.append(d)
            _alerted_tokens[key] = now

    return new_dips
