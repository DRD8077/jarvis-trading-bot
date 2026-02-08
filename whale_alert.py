"""
========================================================================================
  WHALE ALERT ENGINE — Monitor Large SOL Wallet Transactions
========================================================================================

Features:
  1. Track top Solana wallet activity via Solscan/Helius public APIs
  2. Detect large buys/sells on pump.fun tokens
  3. Watch known whale wallets for insider moves
  4. Real-time alerts when whales buy into micro-cap tokens
  5. All amounts in ₹ INR
  6. Whale score — how bullish/bearish is whale activity for a token
"""

import time
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("whale_alert")


# ═══════════════════════════════════════════════════════════════════════════
#  SOLANA WHALE DETECTION via DexScreener + pump.fun signals
# ═══════════════════════════════════════════════════════════════════════════

# Whale thresholds
WHALE_MIN_USD = 10_000       # $10K+ = whale transaction
SHARK_MIN_USD = 5_000        # $5K+ = shark
DOLPHIN_MIN_USD = 1_000      # $1K+ = dolphin

# Track whale activity per token
_whale_activity: Dict[str, List[Dict]] = {}
_whale_activity_ts: Dict[str, float] = {}
WHALE_CACHE_TTL = 60  # 1 min refresh


def detect_whale_activity_from_dex(token_address: str, chain: str = "solana") -> Dict:
    """
    Analyze DexScreener pair data for whale activity signals.
    
    Uses buy/sell ratio, volume spikes, and liquidity changes as proxy
    for whale movements (since direct wallet tracking requires paid APIs).
    """
    from crypto_engine import get_token_pairs, get_usd_inr_rate, fmt_inr

    inr_rate = get_usd_inr_rate()
    pairs = get_token_pairs(chain, token_address)
    if not pairs:
        return {"whale_score": 0, "signals": [], "error": "No pair data"}

    best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))

    vol = best.get("volume", {})
    txns = best.get("txns", {})
    liq = best.get("liquidity", {})
    pc = best.get("priceChange", {})

    vol_m5 = float(vol.get("m5", 0) or 0)
    vol_h1 = float(vol.get("h1", 0) or 0)
    vol_h24 = float(vol.get("h24", 0) or 0)

    buys_m5 = int(txns.get("m5", {}).get("buys", 0) or 0)
    sells_m5 = int(txns.get("m5", {}).get("sells", 0) or 0)
    buys_h1 = int(txns.get("h1", {}).get("buys", 0) or 0)
    sells_h1 = int(txns.get("h1", {}).get("sells", 0) or 0)
    buys_h24 = int(txns.get("h24", {}).get("buys", 0) or 0)
    sells_h24 = int(txns.get("h24", {}).get("sells", 0) or 0)

    liq_usd = float(liq.get("usd", 0) or 0)
    m5_change = float(pc.get("m5", 0) or 0)
    h1_change = float(pc.get("h1", 0) or 0)

    mcap = float(best.get("marketCap", 0) or 0)
    symbol = best.get("baseToken", {}).get("symbol", "?")
    name = best.get("baseToken", {}).get("name", "?")

    whale_score = 0
    signals = []

    # ── VOLUME SPIKE DETECTION ──
    hourly_avg = vol_h24 / 24 if vol_h24 > 0 else 0
    if hourly_avg > 0:
        vol_ratio_h1 = vol_h1 / hourly_avg
        vol_ratio_m5 = (vol_m5 * 12) / hourly_avg if vol_m5 > 0 else 0

        if vol_ratio_m5 > 5:
            whale_score += 25
            signals.append(f"🐋 MASSIVE 5m vol spike: {vol_ratio_m5:.1f}x hourly avg ({fmt_inr(vol_m5 * inr_rate)})")
        elif vol_ratio_m5 > 3:
            whale_score += 15
            signals.append(f"🦈 Big 5m volume: {vol_ratio_m5:.1f}x avg ({fmt_inr(vol_m5 * inr_rate)})")

        if vol_ratio_h1 > 5:
            whale_score += 20
            signals.append(f"🐋 1h vol surge: {vol_ratio_h1:.1f}x avg ({fmt_inr(vol_h1 * inr_rate)})")

    # ── BUY PRESSURE (whale accumulation) ──
    total_m5 = buys_m5 + sells_m5
    if total_m5 > 5:
        buy_ratio_m5 = buys_m5 / total_m5
        if buy_ratio_m5 > 0.8:
            whale_score += 20
            signals.append(f"🟢 Extreme buy pressure 5m: {buy_ratio_m5:.0%} ({buys_m5}B/{sells_m5}S)")
        elif buy_ratio_m5 > 0.65:
            whale_score += 10
            signals.append(f"🟢 Strong buys 5m: {buy_ratio_m5:.0%}")

    total_h1 = buys_h1 + sells_h1
    if total_h1 > 20:
        buy_ratio_h1 = buys_h1 / total_h1
        if buy_ratio_h1 > 0.7:
            whale_score += 15
            signals.append(f"🟢 1h buy dominance: {buy_ratio_h1:.0%} ({buys_h1}B/{sells_h1}S)")
        elif buy_ratio_h1 < 0.3:
            whale_score -= 15
            signals.append(f"🔴 1h sell pressure: {buy_ratio_h1:.0%} — whales dumping?")

    # ── LARGE AVG TRANSACTION SIZE ──
    if total_m5 > 0 and vol_m5 > 0:
        avg_txn_m5 = vol_m5 / total_m5
        if avg_txn_m5 >= WHALE_MIN_USD:
            whale_score += 25
            signals.append(f"🐋 Whale-size txns: avg {fmt_inr(avg_txn_m5 * inr_rate)} per trade")
        elif avg_txn_m5 >= SHARK_MIN_USD:
            whale_score += 15
            signals.append(f"🦈 Shark-size txns: avg {fmt_inr(avg_txn_m5 * inr_rate)} per trade")
        elif avg_txn_m5 >= DOLPHIN_MIN_USD:
            whale_score += 8
            signals.append(f"🐬 Dolphin trades: avg {fmt_inr(avg_txn_m5 * inr_rate)}")

    # ── PRICE + VOLUME DIVERGENCE ──
    if m5_change < -5 and buys_m5 > sells_m5 * 2:
        whale_score += 15
        signals.append(f"🔄 Price dip + heavy buys — whale accumulation pattern")

    if m5_change > 10 and sells_m5 > buys_m5 * 1.5:
        whale_score -= 10
        signals.append(f"⚠️ Price pump + heavy sells — whale distribution warning")

    # ── LIQUIDITY RELATIVE TO MCAP ──
    if mcap > 0 and liq_usd > 0:
        liq_ratio = liq_usd / mcap
        if liq_ratio > 0.3:
            whale_score += 5
            signals.append(f"💧 High liquidity: {liq_ratio:.0%} of MCap")
        elif liq_ratio < 0.05:
            whale_score -= 10
            signals.append(f"⚠️ Very low liquidity: {liq_ratio:.0%} — thin order book")

    whale_score = max(0, min(100, whale_score))

    # Classification
    if whale_score >= 70:
        classification = "🐋🐋🐋 HEAVY WHALE ACTIVITY"
    elif whale_score >= 50:
        classification = "🐋🦈 WHALE ACCUMULATION LIKELY"
    elif whale_score >= 30:
        classification = "🦈 SHARK ACTIVITY"
    elif whale_score >= 15:
        classification = "🐬 MODERATE ACTIVITY"
    else:
        classification = "🐠 RETAIL DOMINATED"

    return {
        "symbol": symbol,
        "name": name,
        "chain": chain,
        "mint": token_address,
        "whale_score": whale_score,
        "classification": classification,
        "signals": signals,
        "vol_m5_usd": vol_m5,
        "vol_h1_usd": vol_h1,
        "vol_h24_usd": vol_h24,
        "buys_m5": buys_m5,
        "sells_m5": sells_m5,
        "buys_h1": buys_h1,
        "sells_h1": sells_h1,
        "liq_usd": liq_usd,
        "mcap_usd": mcap,
        "m5_change": m5_change,
        "h1_change": h1_change,
    }


def scan_whale_activity_trending(limit: int = 10) -> List[Dict]:
    """Scan trending tokens for whale activity and rank by whale score."""
    from crypto_engine import get_top_boosted_tokens, get_token_pairs

    boosted = get_top_boosted_tokens(30)
    results = []

    for token in boosted:
        addr = token.get("tokenAddress", "")
        chain = token.get("chainId", "")
        if not addr or not chain:
            continue

        whale_data = detect_whale_activity_from_dex(addr, chain)
        if whale_data.get("whale_score", 0) >= 10:
            results.append(whale_data)

    results.sort(key=lambda x: x["whale_score"], reverse=True)
    return results[:limit]


# ═══════════════════════════════════════════════════════════════════════════
#  TELEGRAM FORMATTERS (INR)
# ═══════════════════════════════════════════════════════════════════════════

def format_whale_report(whale_data: Dict) -> str:
    """Format single token whale analysis for Telegram."""
    from crypto_engine import fmt_inr, get_usd_inr_rate

    inr_rate = get_usd_inr_rate()
    ws = whale_data["whale_score"]

    msg = (
        f"🐋 *WHALE ANALYSIS — {whale_data['symbol']}* 🐋\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 *{whale_data['symbol']}* ({whale_data.get('name', '')})\n"
        f"🔗 {whale_data.get('chain', '?').upper()}\n\n"
        f"🎯 *Whale Score: {ws}/100*\n"
        f"📊 {whale_data['classification']}\n\n"
    )

    if whale_data.get("signals"):
        msg += "🔍 *Signals Detected:*\n"
        for s in whale_data["signals"]:
            msg += f"   {s}\n"
        msg += "\n"

    msg += (
        f"📊 *Volume:*\n"
        f"   5m: {fmt_inr(whale_data['vol_m5_usd'] * inr_rate)}\n"
        f"   1h: {fmt_inr(whale_data['vol_h1_usd'] * inr_rate)}\n"
        f"   24h: {fmt_inr(whale_data['vol_h24_usd'] * inr_rate)}\n\n"
        f"🛒 *Transactions:*\n"
        f"   5m: {whale_data['buys_m5']}B / {whale_data['sells_m5']}S\n"
        f"   1h: {whale_data['buys_h1']}B / {whale_data['sells_h1']}S\n\n"
        f"💧 Liquidity: {fmt_inr(whale_data['liq_usd'] * inr_rate)}\n"
        f"📊 MCap: {fmt_inr(whale_data['mcap_usd'] * inr_rate)}\n"
    )

    if ws >= 50:
        msg += "\n🐋 *WHALES ARE ACTIVE — Watch closely!*\n"
    elif ws < 15:
        msg += "\n🐠 *No significant whale activity detected.*\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *Whale activity ≠ guaranteed profit. DYOR!*"
    return msg


def format_whale_scan(results: List[Dict]) -> str:
    """Format whale scan results for Telegram."""
    from crypto_engine import fmt_inr, get_usd_inr_rate

    if not results:
        return "🐋 No significant whale activity detected in trending tokens."

    inr_rate = get_usd_inr_rate()
    msg = "🐋🔍 *WHALE ACTIVITY SCANNER* 🔍🐋\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Tracking smart money in trending tokens_\n\n"

    for i, w in enumerate(results[:8], 1):
        ws = w["whale_score"]
        if ws >= 70:
            tier = "🐋🐋🐋"
        elif ws >= 50:
            tier = "🐋🦈"
        elif ws >= 30:
            tier = "🦈"
        else:
            tier = "🐬"

        msg += (
            f"*{i}. {w['symbol']}* ({w.get('chain', '?').upper()}) {tier}\n"
            f"   🎯 Whale Score: {ws}/100\n"
            f"   📊 Vol 1h: {fmt_inr(w['vol_h1_usd'] * inr_rate)} | "
            f"MCap: {fmt_inr(w['mcap_usd'] * inr_rate)}\n"
            f"   🛒 1h: {w['buys_h1']}B/{w['sells_h1']}S\n"
        )
        top_signal = w.get("signals", [""])[0]
        if top_signal:
            msg += f"   ⚡ {top_signal}\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🐋 Higher score = more whale/smart money activity\n"
    msg += "⚠️ *DYOR! Not financial advice.*"
    return msg


# ═══════════════════════════════════════════════════════════════════════════
#  HELIUS / SOLSCAN ON-CHAIN WHALE TRACKING (NEW!)
# ═══════════════════════════════════════════════════════════════════════════

# Known whale wallets (community-tracked large holders)
KNOWN_WHALE_WALLETS = {
    # Top Solana DeFi whales (public)
    "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": "Wintermute",
    "CEQhZ3SJD4KBWT5oYPEEBRm1GYv65KSFg1Z68gLfDNq6": "Jump Trading",
    "FWznbcNXWQuHTawe9RxvQ2LdCENssh12dsznf4RiouN5": "Alameda (remnant)",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "Raydium Whale",
}

def check_helius_transactions(mint_address: str, limit: int = 20) -> List[Dict]:
    """Check recent large transactions for a token via Helius public API.
    Free tier: No key needed for basic queries.
    """
    large_txns = []
    try:
        import os
        helius_key = os.getenv("HELIUS_API_KEY", "")
        
        # Use Helius if key available, else use Solscan public API
        if helius_key:
            url = f"https://api.helius.xyz/v0/addresses/{mint_address}/transactions?api-key={helius_key}&limit={limit}"
        else:
            # Solscan public endpoint (no key, rate limited)
            url = f"https://public-api.solscan.io/token/transfer?tokenAddress={mint_address}&limit={limit}&offset=0"
        
        resp = requests.get(url, timeout=10, headers={
            "Accept": "application/json",
            "User-Agent": "Market-Bot/1.0"
        })
        
        if resp.status_code != 200:
            return large_txns
            
        data = resp.json()
        if not isinstance(data, list):
            data = data.get("data", []) if isinstance(data, dict) else []
        
        for txn in data:
            # Parse Solscan format
            amount = float(txn.get("amount", 0) or txn.get("lamport", 0) or 0)
            src = txn.get("src", "") or txn.get("from_address", "")
            dst = txn.get("dst", "") or txn.get("to_address", "")
            ts = txn.get("blockTime", 0) or txn.get("block_time", 0)
            
            # Check if any known whale is involved
            src_name = KNOWN_WHALE_WALLETS.get(src, "")
            dst_name = KNOWN_WHALE_WALLETS.get(dst, "")
            
            if amount > 0:
                large_txns.append({
                    "amount": amount,
                    "from": src[:8] + "..." if src else "?",
                    "from_name": src_name,
                    "to": dst[:8] + "..." if dst else "?",
                    "to_name": dst_name,
                    "is_known_whale": bool(src_name or dst_name),
                    "timestamp": ts,
                    "direction": "BUY" if dst_name else ("SELL" if src_name else "TRANSFER"),
                })
        
        # Sort by amount descending
        large_txns.sort(key=lambda x: x["amount"], reverse=True)
        
    except Exception as e:
        logger.error(f"Helius/Solscan check failed: {e}")
    
    return large_txns[:10]


def format_onchain_whale_report(mint_address: str, symbol: str = "TOKEN") -> str:
    """Format on-chain whale transaction report."""
    from crypto_engine import get_usd_inr_rate, fmt_inr
    
    txns = check_helius_transactions(mint_address)
    inr_rate = get_usd_inr_rate()
    
    if not txns:
        return f"🐋 *{symbol} ON-CHAIN* — No recent large transactions found."
    
    msg = f"🐋🔗 *{symbol} — ON-CHAIN WHALE MOVES* 🔗🐋\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    known_count = sum(1 for t in txns if t["is_known_whale"])
    if known_count > 0:
        msg += f"👀 *{known_count} Known Whale Transactions!*\n\n"
    
    for i, t in enumerate(txns[:8], 1):
        whale_tag = f" [{t['from_name'] or t['to_name']}]" if t["is_known_whale"] else ""
        direction = {"BUY": "🟢 BUY", "SELL": "🔴 SELL", "TRANSFER": "🔄 XFER"}.get(t["direction"], "🔄")
        
        msg += f"*{i}.* {direction}{whale_tag}\n"
        msg += f"   💰 Amount: {t['amount']:,.2f}\n"
        msg += f"   📤 {t['from']} → 📥 {t['to']}\n"
        if t["timestamp"]:
            dt = datetime.fromtimestamp(t["timestamp"]).strftime("%d %b %H:%M")
            msg += f"   📅 {dt}\n"
        msg += "\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ _On-chain data may be delayed. DYOR!_"
    return msg
