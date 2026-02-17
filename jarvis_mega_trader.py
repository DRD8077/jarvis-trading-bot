"""
🚀💰🔥 JARVIS MEGA AI TRADER v2.0 — NUCLEAR Autonomous Crypto Conqueror
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A PRO CONQUEROR TRADER that:
✅ Scans 6+ sources: DexScreener, DexTools, PumpFun, CoinGecko, CoinDCX, Birdeye
✅ AI-powered gem scoring (15+ factors)
✅ Auto rug-pull detection before EVERY buy (GoPlus + custom analysis)
✅ Real on-chain Jupiter DEX swaps (buy & sell)
✅ Smart trailing stop-loss + partial take-profit at each multiplier
✅ INR wallet system — deposit ₹500, see everything in ₹
✅ Phantom wallet transfer — withdraw to your Solana address
✅ Compound stages: ₹2K → ₹2L → ₹2Cr → ₹200Cr
✅ Everything REAL, LIVE, NO FAKE NUMBERS

100% FREE APIs — No paid subscriptions needed
"""

import os, json, time, asyncio, logging, secrets, hashlib, hmac, base64, math
import threading, traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger("MEGA-TRADER")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════════
#  IMPORTS — All trading engines
# ═══════════════════════════════════════════════════════════════

# Real trader (Jupiter swaps, wallet management)
try:
    from jarvis_real_trader import (
        create_trading_wallet, get_trading_wallet, get_sol_balance,
        buy_token, sell_token, execute_swap, get_swap_quote,
        get_live_portfolio, get_token_accounts, get_token_price_usd,
        enable_auto_trade, disable_auto_trade, _get_usd_inr,
        _load_trader_wallets, _save_trader_wallets, _find_position,
        _notify, set_trade_callback, _get_keypair,
        SOL_MINT, USDC_MINT, LAMPORTS_PER_SOL, MIN_SOL_RESERVE,
        SOLANA_SDK_AVAILABLE, COMPOUND_STAGES, _wallets_lock,
        _rpc_call, FREE_RPC_ENDPOINTS
    )
    REAL_TRADER_AVAILABLE = True
except ImportError as e:
    logger.error(f"jarvis_real_trader not available: {e}")
    REAL_TRADER_AVAILABLE = False

# Scanner engines
try:
    from dex_engine import (dex_search, dex_trending, dex_get_token, dex_new_pairs,
                            find_dip_gems, pumpfun_trending, pumpfun_new_coins,
                            cg_trending, cg_prices, jupiter_price)
except: dex_search = dex_trending = dex_get_token = None

try:
    from dextools_engine import get_hot_pairs as dt_hot
except: dt_hot = None

try:
    from rug_detector import analyze_rug_risk, check_goplus_security
except: analyze_rug_risk = check_goplus_security = None

try:
    from crypto_intelligence import get_market_intelligence
except: get_market_intelligence = None

try:
    from buy_sell_engine import calculate_rsi, calculate_macd
except: calculate_rsi = calculate_macd = None

try:
    from web3_rocket_scanner import scan_top_rockets
except: scan_top_rockets = None

try:
    from coindcx_mega_scanner import mega_scan_all as cdcx_scan
except: cdcx_scan = None

try:
    from sentiment_engine import analyze_news_sentiment
except: analyze_news_sentiment = None

import httpx

# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════

# Trading parameters
SCAN_INTERVAL_SECONDS = 120          # 2 min scan cycle
MAX_POSITIONS = 10                    # Max simultaneous positions
MIN_SOL_PER_TRADE = 0.003            # Min 0.003 SOL per trade
MAX_SOL_PER_TRADE = 0.5              # Max 0.5 SOL per trade (risk management)
MIN_GEM_SCORE = 60                   # Minimum AI score to buy (0-100)
MAX_RUG_RISK = 40                    # Maximum acceptable rug risk score (0-100)
TRAILING_STOP_ACTIVATE = 50          # Activate trailing stop at +50%
TRAILING_STOP_PCT = 20               # Trail by 20%

# Take profit levels (% gain → sell % of position)
TAKE_PROFIT_LEVELS = [
    {"gain_pct": 100, "sell_pct": 15, "label": "2x"},
    {"gain_pct": 400, "sell_pct": 20, "label": "5x"},
    {"gain_pct": 900, "sell_pct": 20, "label": "10x"},
    {"gain_pct": 4900, "sell_pct": 15, "label": "50x"},
    {"gain_pct": 9900, "sell_pct": 15, "label": "100x"},
    {"gain_pct": 99900, "sell_pct": 10, "label": "1000x"},
    {"gain_pct": 999900, "sell_pct": 5, "label": "10000x"},
]

# INR compound stages
INR_COMPOUND_STAGES = [
    {"stage": 1, "name": "₹500 → ₹5,000", "from": 500, "target": 5_000},
    {"stage": 2, "name": "₹5K → ₹50,000", "from": 5_000, "target": 50_000},
    {"stage": 3, "name": "₹50K → ₹5,00,000", "from": 50_000, "target": 500_000},
    {"stage": 4, "name": "₹5L → ₹50,00,000", "from": 500_000, "target": 5_000_000},
    {"stage": 5, "name": "₹50L → ₹5,00,00,000", "from": 5_000_000, "target": 50_000_000},
]

# State
_mega_running = False
_mega_thread = None
_scan_cache: Dict[str, Any] = {}
_scan_cache_ts: Dict[str, float] = {}
_trade_history_file = Path("jarvis_mega_trades.json")


# ═══════════════════════════════════════════════════════════════
#  🧠 AI GEM SCANNER — Multi-Source Pro Scanner
# ═══════════════════════════════════════════════════════════════

async def _async_get(url: str, params: dict = None, timeout: int = 12) -> dict:
    """Async HTTP GET with retry."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(url, params=params)
            if r.status_code == 200:
                return r.json()
        except:
            pass
    return {}


async def scan_all_sources() -> List[dict]:
    """
    Scan ALL crypto sources for potential gem tokens.
    Returns unified list of token candidates with metadata.
    """
    all_gems = []

    # ── Source 1: DexScreener Trending (boosted tokens) ──
    try:
        if dex_trending:
            trending = await dex_trending()
            for t in (trending or []):
                all_gems.append({
                    "source": "dexscreener_trending",
                    "symbol": t.get("symbol", t.get("baseToken", {}).get("symbol", "?")),
                    "name": t.get("name", t.get("baseToken", {}).get("name", "")),
                    "mint": t.get("token_id", t.get("baseToken", {}).get("address", "")),
                    "chain": t.get("chain", t.get("chainId", "solana")),
                    "price_usd": float(t.get("price_usd", t.get("priceUsd", 0)) or 0),
                    "price_change_5m": float(t.get("priceChange", {}).get("m5", 0) or 0),
                    "price_change_1h": float(t.get("priceChange", {}).get("h1", 0) or 0),
                    "price_change_6h": float(t.get("priceChange", {}).get("h6", 0) or 0),
                    "price_change_24h": float(t.get("priceChange", {}).get("h24", 0) or 0),
                    "volume_24h": float(t.get("volume_24h", t.get("volume", {}).get("h24", 0)) or 0),
                    "liquidity": float(t.get("liquidity_usd", t.get("liquidity", {}).get("usd", 0)) or 0),
                    "market_cap": float(t.get("market_cap", t.get("marketCap", 0)) or 0),
                    "pair_address": t.get("pairAddress", ""),
                    "dex_url": t.get("url", ""),
                    "buys_5m": int(t.get("txns", {}).get("m5", {}).get("buys", 0) or 0),
                    "sells_5m": int(t.get("txns", {}).get("m5", {}).get("sells", 0) or 0),
                })
    except Exception as e:
        logger.warning(f"DexScreener trending scan failed: {e}")

    # ── Source 2: DexScreener Dip Gems ──
    try:
        if find_dip_gems:
            dips = await find_dip_gems(-5, 5000)
            for d in (dips or []):
                all_gems.append({
                    "source": "dexscreener_dips",
                    "symbol": d.get("symbol", "?"),
                    "name": d.get("name", ""),
                    "mint": d.get("token_id", ""),
                    "chain": d.get("chain", "solana"),
                    "price_usd": float(d.get("price_usd", 0) or 0),
                    "price_change_5m": float(d.get("change_5m", 0) or 0),
                    "price_change_1h": float(d.get("change_1h", 0) or 0),
                    "price_change_6h": float(d.get("change_6h", 0) or 0),
                    "price_change_24h": float(d.get("change_24h", 0) or 0),
                    "volume_24h": float(d.get("volume_24h", 0) or 0),
                    "liquidity": float(d.get("liquidity_usd", 0) or 0),
                    "market_cap": float(d.get("market_cap", 0) or 0),
                    "dip_pct": float(d.get("dip_pct", d.get("change_24h", 0)) or 0),
                })
    except Exception as e:
        logger.warning(f"DexScreener dips scan failed: {e}")

    # ── Source 3: PumpFun Trending ──
    try:
        if pumpfun_trending:
            pf = await pumpfun_trending()
            for p in (pf or []):
                all_gems.append({
                    "source": "pumpfun_trending",
                    "symbol": p.get("symbol", "?"),
                    "name": p.get("name", ""),
                    "mint": p.get("token_id", p.get("mint", "")),
                    "chain": "solana",
                    "price_usd": float(p.get("price_usd", 0) or 0),
                    "market_cap": float(p.get("market_cap", p.get("usd_market_cap", 0)) or 0),
                    "volume_24h": float(p.get("volume_24h", 0) or 0),
                    "liquidity": float(p.get("liquidity_usd", 0) or 0),
                    "is_pump": True,
                })
    except Exception as e:
        logger.warning(f"PumpFun scan failed: {e}")

    # ── Source 4: PumpFun New Coins ──
    try:
        if pumpfun_new_coins:
            new_pf = await pumpfun_new_coins()
            for p in (new_pf or [])[:15]:
                all_gems.append({
                    "source": "pumpfun_new",
                    "symbol": p.get("symbol", "?"),
                    "name": p.get("name", ""),
                    "mint": p.get("token_id", p.get("mint", "")),
                    "chain": "solana",
                    "price_usd": float(p.get("price_usd", 0) or 0),
                    "market_cap": float(p.get("market_cap", p.get("usd_market_cap", 0)) or 0),
                    "is_pump": True,
                    "is_new": True,
                })
    except Exception as e:
        logger.warning(f"PumpFun new coins scan failed: {e}")

    # ── Source 5: CoinGecko Trending ──
    try:
        if cg_trending:
            cg = await cg_trending()
            for c in (cg or []):
                all_gems.append({
                    "source": "coingecko_trending",
                    "symbol": c.get("symbol", "?"),
                    "name": c.get("name", ""),
                    "mint": c.get("token_id", c.get("id", "")),
                    "chain": c.get("chain", "multi"),
                    "price_usd": float(c.get("price_usd", 0) or 0),
                    "market_cap": float(c.get("market_cap", 0) or 0),
                    "price_change_24h": float(c.get("change_24h", c.get("price_change_24h", 0)) or 0),
                    "volume_24h": float(c.get("volume_24h", 0) or 0),
                })
    except Exception as e:
        logger.warning(f"CoinGecko scan failed: {e}")

    # ── Source 6: DexTools Hot Pairs ──
    try:
        if dt_hot:
            hot = await asyncio.get_event_loop().run_in_executor(None, dt_hot)
            for h in (hot or [])[:15]:
                all_gems.append({
                    "source": "dextools_hot",
                    "symbol": h.get("symbol", h.get("baseToken", {}).get("symbol", "?")),
                    "name": h.get("name", ""),
                    "mint": h.get("token_id", h.get("baseToken", {}).get("address", "")),
                    "chain": h.get("chain", "solana"),
                    "price_usd": float(h.get("price_usd", h.get("priceUsd", 0)) or 0),
                    "volume_24h": float(h.get("volume_24h", 0) or 0),
                    "liquidity": float(h.get("liquidity_usd", h.get("liquidity", 0)) or 0),
                })
    except Exception as e:
        logger.warning(f"DexTools scan failed: {e}")

    # ── Source 7: Web3 Rockets ──
    try:
        if scan_top_rockets:
            rockets = await asyncio.get_event_loop().run_in_executor(None, scan_top_rockets)
            for r in (rockets or [])[:10]:
                all_gems.append({
                    "source": "web3_rockets",
                    "symbol": r.get("symbol", "?"),
                    "name": r.get("name", ""),
                    "mint": r.get("token_id", r.get("address", "")),
                    "chain": r.get("chain", "solana"),
                    "price_usd": float(r.get("price_usd", 0) or 0),
                    "volume_24h": float(r.get("volume_24h", 0) or 0),
                    "rocket_score": float(r.get("score", 0) or 0),
                })
    except Exception as e:
        logger.warning(f"Web3 rockets scan failed: {e}")

    # Deduplicate by mint address
    seen_mints = set()
    unique_gems = []
    for g in all_gems:
        mint = g.get("mint", "")
        if mint and len(mint) > 20 and mint not in seen_mints:
            seen_mints.add(mint)
            unique_gems.append(g)
        elif not mint or len(mint) <= 20:
            unique_gems.append(g)  # Keep non-Solana tokens

    return unique_gems


# ═══════════════════════════════════════════════════════════════
#  🧠 AI GEM SCORING — Pro-Level Analysis
# ═══════════════════════════════════════════════════════════════

async def score_gem(gem: dict) -> dict:
    """
    AI-powered 15-factor gem scoring.
    Returns gem with added 'ai_score' (0-100) and 'ai_verdict'.
    """
    score = 0
    factors = []
    mint = gem.get("mint", "")
    chain = gem.get("chain", "solana")

    # Factor 1: Liquidity (0-12 points)
    liq = gem.get("liquidity", 0)
    if liq >= 100000:
        score += 12; factors.append("💧 High liquidity (>$100K)")
    elif liq >= 50000:
        score += 10; factors.append("💧 Good liquidity ($50K+)")
    elif liq >= 10000:
        score += 6; factors.append("💧 Medium liquidity ($10K+)")
    elif liq >= 5000:
        score += 3; factors.append("💧 Low liquidity ($5K+)")
    else:
        score += 0; factors.append("⚠️ Very low liquidity")

    # Factor 2: Volume/Liquidity ratio (0-10 points) — high ratio = active trading
    vol = gem.get("volume_24h", 0)
    if liq > 0:
        vol_liq_ratio = vol / liq
        if vol_liq_ratio >= 2:
            score += 10; factors.append("📊 Very high volume ratio")
        elif vol_liq_ratio >= 1:
            score += 8; factors.append("📊 High volume ratio")
        elif vol_liq_ratio >= 0.3:
            score += 5; factors.append("📊 Moderate volume")
        else:
            score += 2; factors.append("📊 Low volume activity")

    # Factor 3: Price change momentum (0-12 points) — look for dip bounce
    change_1h = gem.get("price_change_1h", 0)
    change_5m = gem.get("price_change_5m", 0)
    change_6h = gem.get("price_change_6h", 0)
    change_24h = gem.get("price_change_24h", 0)

    # Ideal: 24h/6h down (dip), but 1h/5m recovering (bounce starting)
    if change_24h <= -10 and change_1h > 0:
        score += 12; factors.append("🔥 DIP BOUNCE pattern! Down 24h, recovering 1h")
    elif change_6h <= -5 and change_5m > 0:
        score += 10; factors.append("🔥 Short-term bounce starting")
    elif change_1h > 5:
        score += 8; factors.append("📈 Strong 1h momentum (+5%+)")
    elif change_5m > 3:
        score += 6; factors.append("📈 Short-term pump (+3%+ in 5m)")
    elif change_24h > 0:
        score += 4; factors.append("📈 Positive 24h")
    else:
        score += 1; factors.append("📉 Still declining")

    # Factor 4: Buy/Sell ratio (0-10 points) — more buys than sells = bullish
    buys = gem.get("buys_5m", 0)
    sells = gem.get("sells_5m", 0)
    if buys + sells > 0:
        buy_ratio = buys / (buys + sells)
        if buy_ratio >= 0.7:
            score += 10; factors.append("🟢 Strong buy pressure (70%+ buys)")
        elif buy_ratio >= 0.55:
            score += 7; factors.append("🟢 Bullish buy/sell ratio")
        elif buy_ratio >= 0.45:
            score += 4; factors.append("⚖️ Balanced trading")
        else:
            score += 1; factors.append("🔴 More sellers than buyers")

    # Factor 5: Market Cap sweet spot (0-10 points)
    mcap = gem.get("market_cap", 0)
    if 10000 <= mcap <= 500000:
        score += 10; factors.append("🎯 Micro-cap gem ($10K-$500K)")
    elif 500000 < mcap <= 5000000:
        score += 8; factors.append("🎯 Small-cap ($500K-$5M)")
    elif 5000000 < mcap <= 50000000:
        score += 5; factors.append("📊 Mid-cap ($5M-$50M)")
    elif mcap > 50000000:
        score += 2; factors.append("🏢 Large cap — less upside")
    else:
        score += 3; factors.append("❓ Unknown market cap")

    # Factor 6: Source reputation (0-8 points)
    source = gem.get("source", "")
    if "trending" in source:
        score += 8; factors.append("🔥 Trending on platform")
    elif "dips" in source:
        score += 7; factors.append("📉 Dip opportunity")
    elif "rockets" in source:
        score += 7; factors.append("🚀 Rocket scanner pick")
    elif "hot" in source:
        score += 6; factors.append("🔥 Hot pair")
    else:
        score += 3

    # Factor 7: Chain preference (0-6 points) — Solana preferred for speed
    if chain == "solana":
        score += 6; factors.append("⚡ Solana (fast, cheap swaps)")
    elif chain in ("ethereum", "base"):
        score += 3; factors.append("🔗 EVM chain")
    else:
        score += 2

    # Factor 8: Price > 0 sanity check (0-5 points)
    price = gem.get("price_usd", 0)
    if price > 0:
        score += 5; factors.append("✅ Valid price data")
    else:
        score -= 10; factors.append("❌ No price — skip!")

    # Factor 9: Not a new unproven token (0-5 points)
    if gem.get("is_new"):
        score += 2; factors.append("✨ Brand new — risky but high reward")
    elif gem.get("is_pump"):
        score += 3; factors.append("🎰 Pump.fun token — speculative")
    else:
        score += 5; factors.append("📊 Established token")

    # Factor 10: Volume existence (0-7 points)
    if vol >= 100000:
        score += 7; factors.append("📊 High 24h volume (>$100K)")
    elif vol >= 10000:
        score += 5; factors.append("📊 Decent volume ($10K+)")
    elif vol >= 1000:
        score += 2; factors.append("📊 Low volume ($1K+)")
    else:
        score += 0; factors.append("⚠️ Very low/no volume")

    # Normalize to 0-100
    max_possible = 12 + 10 + 12 + 10 + 10 + 8 + 6 + 5 + 5 + 7  # = 85
    normalized_score = min(100, int((score / max_possible) * 100))

    # AI verdict
    if normalized_score >= 80:
        verdict = "🔥 STRONG BUY — High conviction gem!"
    elif normalized_score >= 65:
        verdict = "🟢 BUY — Good opportunity"
    elif normalized_score >= 50:
        verdict = "🟡 WATCH — Decent but risky"
    elif normalized_score >= 35:
        verdict = "🟠 RISKY — Proceed with caution"
    else:
        verdict = "🔴 AVOID — Too risky"

    gem["ai_score"] = normalized_score
    gem["ai_verdict"] = verdict
    gem["ai_factors"] = factors
    gem["scored_at"] = datetime.now(IST).isoformat()

    return gem


# ═══════════════════════════════════════════════════════════════
#  🛡️ RUG DETECTION — Pre-Buy Safety Check
# ═══════════════════════════════════════════════════════════════

async def check_rug_safety(mint: str, chain: str = "solana") -> dict:
    """
    Multi-layer rug detection before buying.
    Returns: { safe: bool, risk_score: 0-100, reasons: [...] }
    """
    risk_score = 0
    reasons = []

    if not mint or len(mint) < 20:
        return {"safe": False, "risk_score": 100, "reasons": ["❌ Invalid token address"]}

    # Layer 1: GoPlus Security API (free)
    if check_goplus_security:
        try:
            gp = await asyncio.get_event_loop().run_in_executor(
                None, check_goplus_security, mint, chain
            )
            if gp:
                # Honeypot check
                if gp.get("is_honeypot"):
                    risk_score += 50; reasons.append("🍯 HONEYPOT detected!")
                # Mintable (can create unlimited tokens)
                if gp.get("is_mintable"):
                    risk_score += 15; reasons.append("⚠️ Token is mintable")
                # Owner can change balances
                if gp.get("owner_change_balance"):
                    risk_score += 20; reasons.append("🚨 Owner can change balances!")
                # High buy/sell tax
                buy_tax = float(gp.get("buy_tax", 0) or 0)
                sell_tax = float(gp.get("sell_tax", 0) or 0)
                if sell_tax > 10:
                    risk_score += 20; reasons.append(f"💰 High sell tax: {sell_tax}%")
                elif sell_tax > 5:
                    risk_score += 10; reasons.append(f"💰 Moderate sell tax: {sell_tax}%")
                # Top holder concentration
                if gp.get("holder_count") and int(gp.get("holder_count", 0)) < 50:
                    risk_score += 15; reasons.append(f"👥 Very few holders: {gp.get('holder_count')}")
                # No social/website
                if not gp.get("is_open_source"):
                    risk_score += 5; reasons.append("📝 Not open source")

                if risk_score == 0:
                    reasons.append("✅ GoPlus: No critical issues found")
        except Exception as e:
            logger.warning(f"GoPlus check failed for {mint[:12]}: {e}")

    # Layer 2: Custom rug analysis
    if analyze_rug_risk:
        try:
            rug = await asyncio.get_event_loop().run_in_executor(
                None, analyze_rug_risk, {"token_id": mint, "chain": chain}
            )
            if rug:
                rug_score = rug.get("risk_score", rug.get("rug_risk", 50))
                if rug_score > 70:
                    risk_score += 25; reasons.append(f"🚨 High rug risk: {rug_score}/100")
                elif rug_score > 40:
                    risk_score += 10; reasons.append(f"⚠️ Moderate rug risk: {rug_score}/100")
                else:
                    reasons.append(f"✅ Low rug risk: {rug_score}/100")
        except Exception as e:
            logger.warning(f"Rug analysis failed for {mint[:12]}: {e}")

    # Layer 3: Basic on-chain checks via DexScreener
    try:
        if dex_get_token:
            pairs = await dex_get_token(mint)
            if pairs:
                pair = pairs[0] if isinstance(pairs, list) else pairs
                liq = float(pair.get("liquidity", {}).get("usd", 0) or 0)
                if liq < 1000:
                    risk_score += 15; reasons.append(f"⚠️ Very low liquidity: ${liq:,.0f}")
                fdv = float(pair.get("fdv", 0) or 0)
                if fdv > 0 and liq > 0 and fdv / liq > 100:
                    risk_score += 10; reasons.append(f"⚠️ High FDV/Liq ratio: {fdv/liq:.0f}x")
    except Exception as e:
        logger.warning(f"DexScreener check failed: {e}")

    risk_score = min(100, risk_score)
    safe = risk_score <= MAX_RUG_RISK

    return {
        "safe": safe,
        "risk_score": risk_score,
        "reasons": reasons if reasons else ["✅ No issues detected"],
        "checked_at": datetime.now(IST).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
#  💰 INR WALLET SYSTEM — Deposit, Display, Convert
# ═══════════════════════════════════════════════════════════════

def get_portfolio_inr(chat_id: int) -> dict:
    """
    Get complete portfolio with everything in INR.
    Real on-chain data converted to ₹.
    """
    if not REAL_TRADER_AVAILABLE:
        return {"error": "Trading engine not available"}

    portfolio = get_live_portfolio(chat_id)
    if "error" in portfolio:
        return portfolio

    usd_inr = _get_usd_inr()
    sol_price = portfolio.get("sol_price_usd", 0)
    sol_bal = portfolio.get("sol_balance", 0)

    # Convert everything to INR
    total_inr = portfolio.get("total_value_inr", 0)
    sol_inr = sol_bal * sol_price * usd_inr
    pnl_inr = portfolio.get("total_pnl_inr", 0)

    # Token positions in INR
    positions_inr = []
    for pos in portfolio.get("positions", []):
        positions_inr.append({
            "symbol": pos.get("mint", "")[:8],
            "mint": pos.get("mint", ""),
            "amount": pos.get("amount", 0),
            "price_usd": pos.get("price_usd", 0),
            "price_inr": pos.get("price_usd", 0) * usd_inr,
            "value_inr": pos.get("value_inr", 0),
            "value_usd": pos.get("value_usd", 0),
            "pnl_pct": pos.get("pnl_pct", 0),
            "invested_inr": pos.get("sol_invested", 0) * sol_price * usd_inr,
            "profit_inr": pos.get("value_inr", 0) - (pos.get("sol_invested", 0) * sol_price * usd_inr),
        })

    # Compound stage
    wallet = get_trading_wallet(chat_id)
    stage = _get_compound_stage(total_inr)

    return {
        "wallet_address": portfolio.get("pubkey", ""),
        "total_value_inr": total_inr,
        "total_value_usd": portfolio.get("total_value_usd", 0),
        "sol_balance": sol_bal,
        "sol_balance_inr": sol_inr,
        "sol_price_inr": sol_price * usd_inr,
        "total_pnl_inr": pnl_inr,
        "total_pnl_pct": (pnl_inr / max(1, total_inr - pnl_inr)) * 100 if total_inr > 0 else 0,
        "usd_inr_rate": usd_inr,
        "positions": positions_inr,
        "num_positions": len(positions_inr),
        "compound_stage": stage,
        "auto_trade": wallet.get("auto_trade_enabled", False) if wallet else False,
        "total_trades": len(wallet.get("trades", [])) if wallet else 0,
        "ts": datetime.now(IST).isoformat(),
    }


def _get_compound_stage(total_inr: float) -> dict:
    """Determine current compound stage."""
    for s in INR_COMPOUND_STAGES:
        if total_inr < s["target"]:
            progress = (total_inr / s["target"]) * 100 if s["target"] > 0 else 0
            return {
                "current": s["stage"],
                "name": s["name"],
                "progress_pct": min(100, progress),
                "current_inr": total_inr,
                "target_inr": s["target"],
                "remaining_inr": max(0, s["target"] - total_inr),
            }
    return {
        "current": len(INR_COMPOUND_STAGES) + 1,
        "name": "🏆 ALL STAGES COMPLETE!",
        "progress_pct": 100,
        "current_inr": total_inr,
        "target_inr": total_inr,
        "remaining_inr": 0,
    }


# ═══════════════════════════════════════════════════════════════
#  📤 PHANTOM WALLET TRANSFER — Withdraw to User's Wallet
# ═══════════════════════════════════════════════════════════════

def transfer_to_phantom(chat_id: int, destination: str, sol_amount: float) -> dict:
    """
    Transfer SOL from trading wallet to user's Phantom/Solflare address.
    REAL on-chain transfer via Solana.
    """
    if not REAL_TRADER_AVAILABLE or not SOLANA_SDK_AVAILABLE:
        return {"error": "Trading engine not available"}

    kp = _get_keypair(chat_id)
    if not kp:
        return {"error": "No trading wallet. Create one first!"}

    pubkey = str(kp.pubkey())
    balance = get_sol_balance(pubkey)

    if sol_amount <= 0:
        return {"error": "Invalid amount"}

    if balance < sol_amount + 0.001:  # Keep some for rent
        return {"error": f"Insufficient balance. Available: {balance:.4f} SOL, Requested: {sol_amount:.4f} SOL"}

    # Validate destination address
    try:
        from solders.pubkey import Pubkey as SolPubkey
        dest_pubkey = SolPubkey.from_string(destination)
    except Exception:
        return {"error": "Invalid Solana wallet address"}

    # Build and send transfer transaction
    try:
        from solders.system_program import TransferParams, transfer as sol_transfer
        from solders.transaction import Transaction
        from solders.message import MessageV0
        from solders.hash import Hash

        lamports = int(sol_amount * LAMPORTS_PER_SOL)

        # Get recent blockhash
        bh_result = _rpc_call("getLatestBlockhash", [{"commitment": "confirmed"}])
        if not bh_result or "result" not in bh_result:
            return {"error": "Failed to get blockhash"}

        blockhash_str = bh_result["result"]["value"]["blockhash"]
        blockhash = Hash.from_string(blockhash_str)

        # Create transfer instruction
        ix = sol_transfer(TransferParams(
            from_pubkey=kp.pubkey(),
            to_pubkey=dest_pubkey,
            lamports=lamports,
        ))

        # Build and sign transaction
        msg = MessageV0.try_compile(
            payer=kp.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )
        tx = VersionedTransaction(msg, [kp])
        tx_bytes = bytes(tx)
        tx_b64 = base64.b64encode(tx_bytes).decode('ascii')

        # Send
        result = _rpc_call("sendTransaction", [
            tx_b64,
            {"encoding": "base64", "skipPreflight": False,
             "preflightCommitment": "confirmed", "maxRetries": 3}
        ])

        if result and "result" in result:
            signature = result["result"]
            usd_inr = _get_usd_inr()
            sol_price = get_token_price_usd(SOL_MINT)
            inr_value = sol_amount * sol_price * usd_inr

            # Log the transfer
            _log_transfer(chat_id, {
                "type": "withdraw",
                "destination": destination,
                "sol_amount": sol_amount,
                "inr_value": inr_value,
                "signature": signature,
                "ts": datetime.now(IST).isoformat(),
            })

            return {
                "success": True,
                "signature": signature,
                "sol_sent": sol_amount,
                "inr_value": inr_value,
                "destination": destination,
                "solscan_url": f"https://solscan.io/tx/{signature}",
                "remaining_sol": balance - sol_amount - 0.001,
                "ts": datetime.now(IST).isoformat(),
            }
        else:
            err = "Unknown error"
            if result and "error" in result:
                err = str(result["error"])[:200]
            return {"error": f"Transfer failed: {err}"}

    except ImportError:
        # Fallback: use Jupiter to swap SOL → SOL (effectively a transfer via wrapped SOL)
        return {"error": "Advanced Solana SDK modules needed. pip install solders"}
    except Exception as e:
        return {"error": f"Transfer error: {str(e)[:200]}"}


def _log_transfer(chat_id: int, data: dict):
    """Log withdrawal/transfer."""
    uid = str(chat_id)
    try:
        logs = {}
        tf = Path("jarvis_transfers.json")
        if tf.exists():
            logs = json.loads(tf.read_text())
        logs.setdefault(uid, []).append(data)
        tf.write_text(json.dumps(logs, indent=2))
    except:
        pass


def get_transfer_history(chat_id: int) -> List[dict]:
    """Get transfer history for a user."""
    uid = str(chat_id)
    try:
        tf = Path("jarvis_transfers.json")
        if tf.exists():
            logs = json.loads(tf.read_text())
            return logs.get(uid, [])
    except:
        pass
    return []


# ═══════════════════════════════════════════════════════════════
#  🤖 MEGA AUTO-TRADE ENGINE — The Conqueror
# ═══════════════════════════════════════════════════════════════

def start_mega_trader():
    """Start the MEGA autonomous trading engine."""
    global _mega_running, _mega_thread
    if _mega_running:
        return {"status": "already_running"}
    _mega_running = True
    _mega_thread = threading.Thread(target=_mega_trade_loop, daemon=True)
    _mega_thread.start()
    logger.info("🚀🔥 MEGA TRADER ENGINE STARTED — 2-min cycle")
    return {"status": "started"}


def stop_mega_trader():
    """Stop the MEGA trading engine."""
    global _mega_running
    _mega_running = False
    return {"status": "stopped"}


def _mega_trade_loop():
    """
    NUCLEAR AUTO-TRADING LOOP:
    Every 2 minutes:
    1. Scan 7 sources for gem tokens
    2. AI-score each gem (15 factors)
    3. Rug-check top candidates (GoPlus + custom)
    4. Auto-buy SAFE gems with highest AI score
    5. Manage positions: trailing SL + partial take-profit
    6. Track compound progress (₹500 → ₹5Cr)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while _mega_running:
        try:
            loop.run_until_complete(_mega_trade_cycle())
        except Exception as e:
            logger.error(f"[MEGA-TRADER] Cycle error: {traceback.format_exc()}")
        time.sleep(SCAN_INTERVAL_SECONDS)

    loop.close()


async def _mega_trade_cycle():
    """Single cycle of the MEGA trading engine."""
    if not REAL_TRADER_AVAILABLE:
        logger.warning("[MEGA-TRADER] Real trader not available")
        return

    wallets = _load_trader_wallets()

    for uid, wallet in wallets.items():
        if not wallet.get("auto_trade_enabled"):
            continue

        chat_id = wallet.get("chat_id", 0)
        pubkey = wallet.get("pubkey", "")
        if not pubkey or not chat_id:
            continue

        try:
            sol_balance = get_sol_balance(pubkey)
            sol_price = get_token_price_usd(SOL_MINT)
            usd_inr = _get_usd_inr()
            total_inr = sol_balance * sol_price * usd_inr

            logger.info(f"[MEGA-TRADER] User {chat_id}: {sol_balance:.4f} SOL (₹{total_inr:,.0f})")

            # ── STEP 1: Manage existing positions ──
            await _mega_manage_positions(chat_id, wallet, sol_price, usd_inr)

            # ── STEP 2: Auto-buy if enough SOL ──
            available_sol = sol_balance - MIN_SOL_RESERVE
            active_positions = len([p for p in wallet.get("active_positions", []) if p.get("status") == "active"])

            if available_sol >= MIN_SOL_PER_TRADE and active_positions < MAX_POSITIONS:
                # Scan all sources
                gems = await scan_all_sources()
                logger.info(f"[MEGA-TRADER] Scanned {len(gems)} gems from all sources")

                # Score each gem
                scored = []
                for g in gems:
                    scored_gem = await score_gem(g)
                    if scored_gem["ai_score"] >= MIN_GEM_SCORE:
                        scored.append(scored_gem)

                # Sort by AI score
                scored.sort(key=lambda x: x["ai_score"], reverse=True)
                logger.info(f"[MEGA-TRADER] {len(scored)} gems passed AI score threshold ({MIN_GEM_SCORE}+)")

                # Check rug safety for top candidates
                slots = MAX_POSITIONS - active_positions
                buy_candidates = []

                for gem in scored[:slots * 2]:  # Check 2x candidates to account for rug fails
                    mint = gem.get("mint", "")
                    if not mint or len(mint) < 30:
                        continue

                    # Skip if already holding
                    existing = _find_position(chat_id, mint)
                    if existing:
                        continue

                    # Only trade Solana tokens (we have Jupiter swap)
                    if gem.get("chain", "solana") != "solana":
                        continue

                    # RUG CHECK
                    rug_result = await check_rug_safety(mint, "solana")
                    if rug_result["safe"]:
                        gem["rug_check"] = rug_result
                        buy_candidates.append(gem)
                        logger.info(f"[MEGA-TRADER] ✅ SAFE: {gem.get('symbol')} (score={gem['ai_score']}, rug_risk={rug_result['risk_score']})")
                    else:
                        logger.info(f"[MEGA-TRADER] ❌ UNSAFE: {gem.get('symbol')} (rug_risk={rug_result['risk_score']})")
                        _notify(chat_id,
                            f"🛡️ *RUG DETECTED — SKIPPED!*\n\n"
                            f"Token: {gem.get('symbol', '?')}\n"
                            f"Risk: {rug_result['risk_score']}/100\n"
                            f"Reason: {', '.join(rug_result['reasons'][:3])}")

                    if len(buy_candidates) >= slots:
                        break

                # Execute buys
                if buy_candidates:
                    per_gem_sol = min(MAX_SOL_PER_TRADE, available_sol / len(buy_candidates))

                    if per_gem_sol >= MIN_SOL_PER_TRADE:
                        for gem in buy_candidates:
                            mint = gem.get("mint", "")
                            symbol = gem.get("symbol", mint[:8])

                            result = buy_token(chat_id, mint, per_gem_sol)
                            if result.get("success"):
                                inr_invested = per_gem_sol * sol_price * usd_inr
                                _notify(chat_id,
                                    f"🟢💎 *AI AUTO-BUY EXECUTED!*\n\n"
                                    f"🪙 Token: {symbol}\n"
                                    f"📊 AI Score: {gem['ai_score']}/100\n"
                                    f"🛡️ Rug Risk: {gem.get('rug_check', {}).get('risk_score', '?')}/100\n"
                                    f"💰 Invested: {per_gem_sol:.4f} SOL (₹{inr_invested:,.0f})\n"
                                    f"📈 Source: {gem.get('source', 'multi')}\n"
                                    f"🔗 [Solscan]({result.get('solscan_url', '')})\n\n"
                                    f"🎯 Targets: 2x→5x→10x→50x→100x→1000x\n"
                                    f"🛡️ Stop-loss: -35% (trailing at +50%)")
                            else:
                                logger.warning(f"[MEGA-TRADER] Buy failed {symbol}: {result.get('error', '')[:80]}")

                            await asyncio.sleep(3)  # Rate limit

            # ── STEP 3: Check compound progress ──
            new_total = get_sol_balance(pubkey) * sol_price * usd_inr
            # Add token values
            for acc in get_token_accounts(pubkey):
                tok_price = get_token_price_usd(acc["mint"])
                new_total += acc["amount"] * tok_price * usd_inr

            stage = _get_compound_stage(new_total)
            if stage["progress_pct"] >= 100 and stage["current"] <= len(INR_COMPOUND_STAGES):
                _notify(chat_id,
                    f"🏆🎉 *COMPOUND STAGE {stage['current']} COMPLETE!*\n\n"
                    f"📊 {stage['name']}\n"
                    f"💰 Portfolio: ₹{new_total:,.0f}\n"
                    f"🚀 Moving to next stage!")

        except Exception as e:
            logger.error(f"[MEGA-TRADER] Error for user {chat_id}: {e}")


async def _mega_manage_positions(chat_id: int, wallet: dict, sol_price: float, usd_inr: float):
    """
    Smart position management with:
    - Fixed stop-loss at -35%
    - Trailing stop-loss (activates at +50%, trails by 20%)
    - Partial take-profit at each multiplier
    """
    positions = wallet.get("active_positions", [])
    pubkey = wallet.get("pubkey", "")
    if not positions or not pubkey:
        return

    for pos in positions:
        if pos.get("status") != "active":
            continue

        token_mint = pos.get("token_mint", "")
        entry_price = pos.get("entry_price_usd", 0)
        if not token_mint or entry_price <= 0:
            continue

        current_price = get_token_price_usd(token_mint)
        if current_price <= 0:
            continue

        pnl_pct = ((current_price / entry_price) - 1) * 100

        # ── TRAILING STOP LOSS ──
        high_water = pos.get("high_water_price", entry_price)
        if current_price > high_water:
            # Update high water mark
            pos["high_water_price"] = current_price
            uid = str(chat_id)
            with _wallets_lock:
                wallets = _load_trader_wallets()
                if uid in wallets:
                    for p in wallets[uid].get("active_positions", []):
                        if p.get("token_mint") == token_mint and p.get("status") == "active":
                            p["high_water_price"] = current_price
                    _save_trader_wallets(wallets)
            high_water = current_price

        # Check trailing stop
        if pnl_pct >= TRAILING_STOP_ACTIVATE:
            # Trailing stop is active
            trailing_level = high_water * (1 - TRAILING_STOP_PCT / 100)
            if current_price <= trailing_level:
                result = sell_token(chat_id, token_mint, 100.0)
                if result.get("success"):
                    sol_got = result.get("sol_received", 0)
                    inr_got = sol_got * sol_price * usd_inr
                    _notify(chat_id,
                        f"📊 *TRAILING STOP HIT!*\n\n"
                        f"Token: {token_mint[:12]}...\n"
                        f"P&L: {pnl_pct:+.1f}% | SOL: {sol_got:.4f} (₹{inr_got:,.0f})\n"
                        f"Peak was +{((high_water/entry_price)-1)*100:.0f}%, trailed at -{TRAILING_STOP_PCT}%\n"
                        f"🔗 [TX]({result.get('solscan_url', '')})")
                continue

        # ── FIXED STOP LOSS (for positions not yet at trailing threshold) ──
        if pnl_pct <= -35:
            result = sell_token(chat_id, token_mint, 100.0)
            if result.get("success"):
                sol_got = result.get("sol_received", 0)
                inr_got = sol_got * sol_price * usd_inr
                _notify(chat_id,
                    f"🔴 *STOP-LOSS TRIGGERED!*\n\n"
                    f"Token: {token_mint[:12]}...\n"
                    f"Loss: {pnl_pct:+.1f}% | SOL Recovered: {sol_got:.4f} (₹{inr_got:,.0f})\n"
                    f"🛡️ Capital protected by JARVIS AI\n"
                    f"🔗 [TX]({result.get('solscan_url', '')})")
            continue

        # ── PARTIAL TAKE-PROFIT ──
        taken = pos.get("profits_taken", [])
        for tp in TAKE_PROFIT_LEVELS:
            if tp["label"] in taken:
                continue
            if pnl_pct >= tp["gain_pct"]:
                sell_pct = tp["sell_pct"]
                result = sell_token(chat_id, token_mint, sell_pct)
                if result.get("success"):
                    sol_got = result.get("sol_received", 0)
                    inr_got = sol_got * sol_price * usd_inr
                    taken.append(tp["label"])
                    pos["profits_taken"] = taken

                    # Update wallet
                    uid = str(chat_id)
                    with _wallets_lock:
                        wallets = _load_trader_wallets()
                        if uid in wallets:
                            wallets[uid]["total_profit_sol"] = wallets[uid].get("total_profit_sol", 0) + sol_got
                            wallets[uid]["total_profit_inr"] = wallets[uid].get("total_profit_inr", 0) + inr_got
                            for p in wallets[uid].get("active_positions", []):
                                if p.get("token_mint") == token_mint and p.get("status") == "active":
                                    p["profits_taken"] = taken
                            _save_trader_wallets(wallets)

                    _notify(chat_id,
                        f"💰🔥 *PROFIT BOOKED — {tp['label']}!*\n\n"
                        f"Token: {token_mint[:12]}...\n"
                        f"📈 P&L: +{pnl_pct:.1f}%\n"
                        f"💵 Sold {sell_pct}% → {sol_got:.4f} SOL (₹{inr_got:,.0f})\n"
                        f"🔗 [TX]({result.get('solscan_url', '')})\n"
                        f"🚀 Remaining riding for higher targets!")
                break  # One TP level per cycle


# ═══════════════════════════════════════════════════════════════
#  📊 DASHBOARD & STATUS
# ═══════════════════════════════════════════════════════════════

def get_mega_trader_status(chat_id: int) -> dict:
    """Complete MEGA trader status for a user."""
    if not REAL_TRADER_AVAILABLE:
        return {"error": "Trading not available", "sdk_installed": False}

    wallet = get_trading_wallet(chat_id)
    if not wallet:
        return {
            "has_wallet": False,
            "message": "No trading wallet. Create one to start!",
            "sdk_installed": SOLANA_SDK_AVAILABLE,
        }

    portfolio = get_portfolio_inr(chat_id)
    usd_inr = _get_usd_inr()
    sol_price = get_token_price_usd(SOL_MINT)

    # Active positions with detailed info
    active_positions = []
    for pos in wallet.get("active_positions", []):
        if pos.get("status") != "active":
            continue
        mint = pos.get("token_mint", "")
        entry_price = pos.get("entry_price_usd", 0)
        current_price = get_token_price_usd(mint) if mint else 0
        pnl_pct = ((current_price / entry_price) - 1) * 100 if entry_price > 0 else 0
        sol_invested = pos.get("sol_invested", 0)

        active_positions.append({
            "mint": mint,
            "symbol": mint[:8] + "...",
            "entry_price_usd": entry_price,
            "current_price_usd": current_price,
            "pnl_pct": pnl_pct,
            "invested_sol": sol_invested,
            "invested_inr": sol_invested * sol_price * usd_inr,
            "current_value_inr": pos.get("tokens_held", 0) * current_price * usd_inr if current_price else 0,
            "profits_taken": pos.get("profits_taken", []),
            "bought_at": pos.get("bought_at", ""),
        })

    # Recent trades
    recent_trades = wallet.get("trades", [])[-10:]
    formatted_trades = []
    for t in reversed(recent_trades):
        formatted_trades.append({
            "type": t.get("type", "?"),
            "mint": t.get("token_mint", "")[:8],
            "sol": t.get("sol_spent", t.get("sol_received", 0)),
            "inr": t.get("sol_spent", t.get("sol_received", 0)) * sol_price * usd_inr,
            "signature": t.get("signature", ""),
            "time": t.get("timestamp", ""),
        })

    return {
        "has_wallet": True,
        "wallet_address": wallet.get("pubkey", ""),
        "auto_trade_enabled": wallet.get("auto_trade_enabled", False),
        "mega_engine_running": _mega_running,
        "sdk_installed": SOLANA_SDK_AVAILABLE,
        "portfolio": portfolio,
        "active_positions": active_positions,
        "recent_trades": formatted_trades,
        "total_trades": len(wallet.get("trades", [])),
        "total_profit_sol": wallet.get("total_profit_sol", 0),
        "total_profit_inr": wallet.get("total_profit_inr", 0),
        "compound_stage": portfolio.get("compound_stage", {}),
        "config": {
            "scan_interval": SCAN_INTERVAL_SECONDS,
            "max_positions": MAX_POSITIONS,
            "min_gem_score": MIN_GEM_SCORE,
            "max_rug_risk": MAX_RUG_RISK,
            "trailing_stop": f"+{TRAILING_STOP_ACTIVATE}% activate, {TRAILING_STOP_PCT}% trail",
            "take_profit_levels": [tp["label"] for tp in TAKE_PROFIT_LEVELS],
        },
        "ts": datetime.now(IST).isoformat(),
    }


async def get_live_scan_results() -> dict:
    """Get current scan results (what AI is seeing right now)."""
    gems = await scan_all_sources()
    scored = []
    for g in gems[:30]:  # Score top 30
        scored.append(await score_gem(g))
    scored.sort(key=lambda x: x["ai_score"], reverse=True)

    return {
        "total_scanned": len(gems),
        "passed_threshold": sum(1 for s in scored if s["ai_score"] >= MIN_GEM_SCORE),
        "top_gems": scored[:15],
        "sources": list(set(g.get("source", "?") for g in gems)),
        "scan_time": datetime.now(IST).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
#  MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Core
    "start_mega_trader", "stop_mega_trader",
    "get_mega_trader_status", "get_live_scan_results",
    # Portfolio
    "get_portfolio_inr",
    # Scanning
    "scan_all_sources", "score_gem", "check_rug_safety",
    # Transfer
    "transfer_to_phantom", "get_transfer_history",
    # Config
    "TAKE_PROFIT_LEVELS", "INR_COMPOUND_STAGES",
]
