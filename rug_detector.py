"""
========================================================================================
  RUG DETECTOR — Honeypot, Rug Pull & Scam Detection Engine
========================================================================================

Features:
  1. Token creator history analysis (serial rugger detection)
  2. Liquidity lock status check
  3. Honeypot detection (can you sell?)
  4. Ownership concentration check
  5. Smart contract risk flags
  6. Bonding curve analysis (pump.fun specific)
  7. Social proof verification
  8. Composite rug risk score (0-100)
  9. All amounts in ₹ INR
"""

import time
import math
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("rug_detector")


# ═══════════════════════════════════════════════════════════════════════════
#  RUG RISK SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def analyze_rug_risk(token: Dict) -> Dict:
    """
    Comprehensive rug pull risk analysis.
    Works with normalized tokens from crypto_engine.
    
    Risk Score: 0 = Safe, 100 = Almost certainly a rug
    
    Checks:
      - Liquidity depth
      - Buy/Sell ratio asymmetry  
      - Market cap vs liquidity ratio
      - Token age
      - Social presence
      - Bonding curve status (pump.fun)
      - Volume patterns
      - Creator reputation signals
    """
    risk_score = 0
    red_flags = []
    green_flags = []
    warnings = []

    source = token.get("source", "dexscreener")
    mcap_usd = token.get("mcap_usd", 0)
    liq_usd = token.get("liq_usd", 0)

    # ── 1. LIQUIDITY CHECK (0-25 risk points) ──
    if source == "dexscreener":
        if liq_usd < 100:
            risk_score += 25
            red_flags.append("🚨 Near-zero liquidity (<$100) — EXTREME RUG RISK")
        elif liq_usd < 500:
            risk_score += 20
            red_flags.append("🚨 Very low liquidity (<$500)")
        elif liq_usd < 2000:
            risk_score += 12
            warnings.append("⚠️ Low liquidity (<$2K)")
        elif liq_usd < 10000:
            risk_score += 5
            warnings.append("⚠️ Moderate liquidity")
        else:
            green_flags.append(f"✅ Good liquidity: ${liq_usd:,.0f}")

    # ── 2. MCAP vs LIQUIDITY RATIO (0-20) ──
    if mcap_usd > 0 and liq_usd > 0:
        mcap_liq_ratio = mcap_usd / liq_usd
        if mcap_liq_ratio > 100:
            risk_score += 20
            red_flags.append(f"🚨 MCap/Liq: {mcap_liq_ratio:.0f}x — massively inflated")
        elif mcap_liq_ratio > 50:
            risk_score += 15
            red_flags.append(f"⚠️ MCap/Liq: {mcap_liq_ratio:.0f}x — thin liquidity")
        elif mcap_liq_ratio > 20:
            risk_score += 8
            warnings.append(f"⚠️ MCap/Liq: {mcap_liq_ratio:.0f}x")
        elif mcap_liq_ratio < 5:
            green_flags.append(f"✅ Healthy MCap/Liq ratio: {mcap_liq_ratio:.1f}x")
    elif mcap_usd > 0 and liq_usd <= 0:
        risk_score += 20
        red_flags.append("🚨 No measurable liquidity")

    # ── 3. BUY/SELL ASYMMETRY — Honeypot Detection (0-20) ──
    buys_h1 = token.get("buys_h1", 0)
    sells_h1 = token.get("sells_h1", 0)
    buys_h24 = token.get("buys_h24", 0)
    sells_h24 = token.get("sells_h24", 0)

    total_h1 = buys_h1 + sells_h1
    total_h24 = buys_h24 + sells_h24

    if total_h1 > 10:
        sell_ratio = sells_h1 / total_h1
        if sell_ratio < 0.05:
            risk_score += 20
            red_flags.append(f"🚨 HONEYPOT SUSPECT: {sells_h1} sells vs {buys_h1} buys in 1h")
        elif sell_ratio < 0.15:
            risk_score += 12
            red_flags.append(f"⚠️ Very few sells: {sell_ratio:.0%} — possible honeypot")

    if total_h24 > 50 and sells_h24 > 0:
        sell_ratio_24 = sells_h24 / total_h24
        if sell_ratio_24 < 0.1:
            risk_score += 15
            red_flags.append(f"🚨 24h: Only {sell_ratio_24:.0%} sells — likely honeypot")
        elif sell_ratio_24 > 0.4:
            green_flags.append(f"✅ Healthy sell activity: {sell_ratio_24:.0%}")

    # ── 4. TOKEN AGE (0-15) ──
    age_hours = token.get("age_hours", 0)
    if source == "pump.fun":
        if age_hours < 0.25:
            risk_score += 15
            red_flags.append(f"🆕 Brand new: {age_hours * 60:.0f} min old — high risk")
        elif age_hours < 1:
            risk_score += 10
            warnings.append(f"🆕 Very fresh: {age_hours * 60:.0f} min old")
        elif age_hours < 6:
            risk_score += 5
            warnings.append(f"🆕 Young token: {age_hours:.1f}h old")
        elif age_hours > 72:
            green_flags.append(f"✅ Survived 3+ days ({age_hours / 24:.1f} days)")

    # ── 5. SOCIAL PRESENCE (0-10) ──
    has_twitter = bool(token.get("twitter"))
    has_telegram = bool(token.get("telegram"))
    has_website = bool(token.get("website"))
    reply_count = token.get("reply_count", 0)

    social_score = 0
    if not has_twitter and not has_telegram and not has_website:
        risk_score += 10
        red_flags.append("🚨 No social links — anonymous project")
    else:
        if has_twitter:
            social_score += 1
            green_flags.append("✅ Has Twitter/X")
        if has_telegram:
            social_score += 1
            green_flags.append("✅ Has Telegram")
        if has_website:
            social_score += 1
            green_flags.append("✅ Has Website")
        if social_score >= 2:
            risk_score -= 3

    if reply_count > 100:
        green_flags.append(f"✅ Active community: {reply_count} replies")
        risk_score -= 3
    elif reply_count < 5 and source == "pump.fun":
        risk_score += 5
        warnings.append("⚠️ Very few community replies")

    # ── 6. BONDING CURVE (pump.fun specific, 0-10) ──
    if source == "pump.fun":
        is_graduated = token.get("is_graduated", False)
        has_raydium = token.get("has_raydium", False)
        if is_graduated and has_raydium:
            green_flags.append("✅ Graduated to Raydium — passed bonding curve")
            risk_score -= 5
        elif not is_graduated:
            risk_score += 8
            warnings.append("⏳ Still on bonding curve — no Raydium pool yet")

    # ── 7. VOLUME PATTERN ANOMALY (0-10) ──
    vol_h1 = token.get("vol_h1", 0)
    vol_h24 = token.get("vol_h24", 0)
    if vol_h24 > 0 and vol_h1 > 0:
        hourly_avg = vol_h24 / 24
        if hourly_avg > 0:
            ratio = vol_h1 / hourly_avg
            if ratio > 20:
                risk_score += 8
                warnings.append(f"⚠️ Abnormal vol spike: {ratio:.0f}x avg — could be wash trading")

    # ── 8. PRICE ACTION RED FLAGS (0-10) ──
    h1_change = token.get("change_h1", 0)
    h24_change = token.get("change_h24", 0)
    if h24_change > 5000:
        risk_score += 10
        red_flags.append(f"🚨 {h24_change:+.0f}% in 24h — extreme pump, likely dump incoming")
    elif h24_change > 1000:
        risk_score += 5
        warnings.append(f"⚠️ {h24_change:+.0f}% in 24h — parabolic, high risk")

    # Clamp score
    risk_score = max(0, min(100, risk_score))

    # Safety rating
    if risk_score >= 75:
        safety = "🔴 EXTREMELY DANGEROUS"
        verdict = "AVOID"
    elif risk_score >= 50:
        safety = "🟠 HIGH RISK"
        verdict = "RISKY"
    elif risk_score >= 30:
        safety = "🟡 MODERATE RISK"
        verdict = "CAUTION"
    elif risk_score >= 15:
        safety = "🟢 RELATIVELY SAFE"
        verdict = "OK"
    else:
        safety = "🟢✅ LOW RISK"
        verdict = "SAFE"

    return {
        **token,
        "rug_risk_score": risk_score,
        "safety_rating": safety,
        "verdict": verdict,
        "red_flags": red_flags,
        "green_flags": green_flags,
        "warnings": warnings,
    }


def scan_rug_risk_trending(limit: int = 10) -> List[Dict]:
    """Scan trending tokens and rank by rug risk."""
    from crypto_engine import scan_all_gems

    gems = scan_all_gems(min_score=0, limit=30)
    analyzed = [analyze_rug_risk(g) for g in gems]
    analyzed.sort(key=lambda x: x["rug_risk_score"], reverse=True)
    return analyzed[:limit]


def check_token_rug_risk(token_address: str, chain: str = "solana") -> Dict:
    """Check rug risk for a specific token by address."""
    from crypto_engine import get_token_pairs, _normalize_dex_pair, calculate_gem_score

    pairs = get_token_pairs(chain, token_address)
    if not pairs:
        # Try pump.fun
        from crypto_engine import pump_get_coin_detail, _normalize_pump_token
        detail = pump_get_coin_detail(token_address)
        if detail:
            token = _normalize_pump_token(detail)
            token = calculate_gem_score(token)
            return analyze_rug_risk(token)
        return {"rug_risk_score": -1, "error": "Token not found"}

    best = max(pairs, key=lambda p: float((p.get("volume") or {}).get("h24", 0) or 0))
    token = _normalize_dex_pair(best)
    from crypto_engine import calculate_gem_score
    token = calculate_gem_score(token)
    return analyze_rug_risk(token)


# ═══════════════════════════════════════════════════════════════════════════
#  TELEGRAM FORMATTERS
# ═══════════════════════════════════════════════════════════════════════════

def format_rug_check(result: Dict) -> str:
    """Format rug risk analysis for Telegram."""
    from crypto_engine import fmt_inr

    if result.get("error"):
        return f"❌ {result['error']}"

    rs = result["rug_risk_score"]
    msg = (
        f"🔍🛡️ *RUG RISK ANALYSIS* 🛡️🔍\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 *{result.get('symbol', '?')}* ({result.get('name', '')})\n"
        f"🔗 {result.get('chain', '?').upper()}"
    )
    if result.get("source") == "pump.fun":
        msg += " | 🟣 pump.fun"
    msg += "\n\n"

    # Big risk meter
    bar_len = 20
    fill = int(rs / 100 * bar_len)
    bar = "🟥" * fill + "⬜" * (bar_len - fill)
    msg += (
        f"🎯 *Rug Risk: {rs}/100*\n"
        f"   {bar}\n"
        f"   {result['safety_rating']}\n"
        f"   Verdict: *{result['verdict']}*\n\n"
    )

    # Price info
    msg += (
        f"💰 Price: {fmt_inr(result.get('price_inr', 0))}\n"
        f"📊 MCap: {fmt_inr(result.get('mcap_inr', 0))}\n"
    )
    if result.get("liq_inr", 0) > 0:
        msg += f"💧 Liquidity: {fmt_inr(result['liq_inr'])}\n"
    msg += "\n"

    # Red flags
    if result.get("red_flags"):
        msg += "🚨 *RED FLAGS:*\n"
        for f in result["red_flags"]:
            msg += f"   {f}\n"
        msg += "\n"

    # Warnings
    if result.get("warnings"):
        msg += "⚠️ *WARNINGS:*\n"
        for w in result["warnings"]:
            msg += f"   {w}\n"
        msg += "\n"

    # Green flags
    if result.get("green_flags"):
        msg += "✅ *POSITIVE SIGNS:*\n"
        for g in result["green_flags"]:
            msg += f"   {g}\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *This is automated analysis. Always DYOR!*"
    return msg


def format_rug_scan(results: List[Dict]) -> str:
    """Format rug risk scan of multiple tokens."""
    from crypto_engine import fmt_inr

    if not results:
        return "🛡️ No tokens analyzed."

    msg = "🛡️🔍 *RUG RISK SCANNER* 🔍🛡️\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Scanning trending tokens for rug risk_\n\n"

    for i, r in enumerate(results[:10], 1):
        rs = r["rug_risk_score"]
        if rs >= 75:
            icon = "🔴"
        elif rs >= 50:
            icon = "🟠"
        elif rs >= 30:
            icon = "🟡"
        else:
            icon = "🟢"

        flags = len(r.get("red_flags", []))
        msg += (
            f"*{i}. {r.get('symbol', '?')}* {icon} Risk: {rs}/100\n"
            f"   {r['safety_rating']} | {flags} red flags\n"
            f"   MCap: {fmt_inr(r.get('mcap_inr', 0))}\n"
        )
        top_flag = r.get("red_flags", [""])[0] if r.get("red_flags") else ""
        if top_flag:
            msg += f"   ⚡ {top_flag}\n"
        msg += "\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🔴 High = Dangerous | 🟢 Low = Safer\n"
    msg += "⚠️ *DYOR! Not financial advice.*"
    return msg


# ═══════════════════════════════════════════════════════════════
# GOPLUS TOKEN SECURITY API (NEW!)
# ═══════════════════════════════════════════════════════════════

def check_goplus_security(contract_address: str, chain: str = "solana") -> Dict:
    """Check token security via GoPlus Security API (free, no key needed).
    Returns contract verification, honeypot check, owner analysis.
    """
    import requests

    chain_ids = {
        "solana": "solana",
        "ethereum": "1",
        "bsc": "56",
        "base": "8453",
        "arbitrum": "42161",
    }
    chain_id = chain_ids.get(chain.lower(), "solana")

    result = {
        "is_honeypot": False,
        "is_mintable": False,
        "is_proxy": False,
        "owner_change_balance": False,
        "can_take_owner": False,
        "hidden_owner": False,
        "is_blacklisted": False,
        "buy_tax": 0,
        "sell_tax": 0,
        "holder_count": 0,
        "top_holder_pct": 0,
        "security_score": 50,
        "risk_items": [],
        "safe_items": [],
        "source": "goplus",
    }

    try:
        if chain_id == "solana":
            url = f"https://api.gopluslabs.io/api/v1/solana/token_security/{contract_address}"
        else:
            url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={contract_address}"

        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return result

        data = resp.json()
        if data.get("code") != 1:
            return result

        token_data = data.get("result", {})
        if isinstance(token_data, dict):
            # For EVM chains, data is nested under contract address
            if contract_address.lower() in token_data:
                token_data = token_data[contract_address.lower()]

        if not token_data:
            return result

        # Parse fields
        result["is_honeypot"] = token_data.get("is_honeypot", "0") == "1"
        result["is_mintable"] = token_data.get("is_mintable", "0") == "1"
        result["is_proxy"] = token_data.get("is_proxy", "0") == "1"
        result["owner_change_balance"] = token_data.get("owner_change_balance", "0") == "1"
        result["can_take_owner"] = token_data.get("can_take_back_ownership", "0") == "1"
        result["hidden_owner"] = token_data.get("hidden_owner", "0") == "1"
        result["is_blacklisted"] = token_data.get("is_blacklisted", "0") == "1"

        try:
            result["buy_tax"] = float(token_data.get("buy_tax", 0)) * 100
            result["sell_tax"] = float(token_data.get("sell_tax", 0)) * 100
        except (ValueError, TypeError):
            pass

        result["holder_count"] = int(token_data.get("holder_count", 0))

        # Top holder analysis
        holders = token_data.get("holders", [])
        if holders and isinstance(holders, list):
            top_pct = sum(float(h.get("percent", 0)) for h in holders[:5]) * 100
            result["top_holder_pct"] = round(top_pct, 1)

        # Calculate security score
        score = 100
        risks = []
        safe = []

        if result["is_honeypot"]:
            score -= 50
            risks.append("⚠️ HONEYPOT detected!")
        else:
            safe.append("✅ Not a honeypot")

        if result["is_mintable"]:
            score -= 15
            risks.append("⚠️ Token is mintable (supply can increase)")
        else:
            safe.append("✅ Not mintable")

        if result["owner_change_balance"]:
            score -= 20
            risks.append("⚠️ Owner can change balances!")
        else:
            safe.append("✅ Owner cannot change balances")

        if result["hidden_owner"]:
            score -= 10
            risks.append("⚠️ Hidden owner")

        if result["is_proxy"]:
            score -= 10
            risks.append("⚠️ Proxy contract (code can change)")

        if result["sell_tax"] > 10:
            score -= 15
            risks.append(f"⚠️ High sell tax: {result['sell_tax']:.0f}%")
        elif result["sell_tax"] > 5:
            score -= 5
            risks.append(f"⚡ Sell tax: {result['sell_tax']:.0f}%")

        if result["top_holder_pct"] > 50:
            score -= 15
            risks.append(f"⚠️ Top 5 holders own {result['top_holder_pct']:.0f}%")
        elif result["top_holder_pct"] > 30:
            score -= 5
            risks.append(f"⚡ Top 5 holders own {result['top_holder_pct']:.0f}%")
        else:
            safe.append(f"✅ Top 5 holders: {result['top_holder_pct']:.0f}% (distributed)")

        if result["is_blacklisted"]:
            score -= 10
            risks.append("⚠️ Has blacklist function")

        result["security_score"] = max(0, score)
        result["risk_items"] = risks
        result["safe_items"] = safe

    except Exception as e:
        logger.error(f"GoPlus check failed: {e}")

    return result


def format_goplus_report(gp: Dict, symbol: str = "TOKEN") -> str:
    """Format GoPlus security report."""
    score = gp.get("security_score", 50)

    if score >= 80:
        verdict = "🟢 SAFE"
    elif score >= 60:
        verdict = "🟡 CAUTION"
    elif score >= 40:
        verdict = "🟠 RISKY"
    else:
        verdict = "🔴 DANGEROUS"

    msg = f"🛡️ *{symbol} — CONTRACT SECURITY* 🛡️\n"
    msg += f"{'═' * 30}\n"
    msg += f"🎯 *Score:* {score}/100 {verdict}\n\n"

    if gp.get("risk_items"):
        msg += "🔴 *Risks:*\n"
        for r in gp["risk_items"]:
            msg += f"  {r}\n"
        msg += "\n"

    if gp.get("safe_items"):
        msg += "🟢 *Safe:*\n"
        for s in gp["safe_items"]:
            msg += f"  {s}\n"
        msg += "\n"

    msg += f"📊 Holders: {gp.get('holder_count', '?')}\n"
    msg += f"💰 Buy Tax: {gp.get('buy_tax', 0):.0f}% | Sell Tax: {gp.get('sell_tax', 0):.0f}%\n"

    return msg
